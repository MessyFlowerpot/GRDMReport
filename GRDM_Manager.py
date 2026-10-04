import subprocess
import time
import os
import re
import sys
import signal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
TUNNEL_CMD = "cloudflared"

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[G.R.D.M.] [ERROR] 未找到 GITHUB_TOKEN！")
        sys.exit(1)
    return token.strip()

def update_index_html(tunnel_url):
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = re.sub(
            r'const\s+TUNNEL_URL\s*=\s*"[^"]*"',
            f'const TUNNEL_URL = "{tunnel_url}"',
            content
        )

        if new_content != content:
            with open(INDEX_PATH, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"[G.R.D.M.] [OK] index.html 已更新为: {tunnel_url}")
            return True
        return False
    except Exception as e:
        print(f"[G.R.D.M.] [ERROR] 更新 HTML 失败: {e}")
        return False

def push_to_github():
    token = get_token()
    auth_url = f"https://{token}@github.com/MessyFlowerpot/GRDMReport.git"
    
    print("[G.R.D.M.] [INFO] 正在同步至 GitHub Pages...")
    
    # Git Add & Commit
    subprocess.run(["git", "add", "."], cwd=BASE_DIR, capture_output=True)
    diff_res = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=BASE_DIR, capture_output=True)
    
    if diff_res.returncode != 0:
        commit_msg = f"Auto-Update: {time.strftime('%H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE_DIR, capture_output=True)
        print("[G.R.D.M.] [DONE] Git 提交成功")
    
    # Git Push
    p_res = subprocess.run(["git", "push", auth_url, "main"], cwd=BASE_DIR, capture_output=True, text=True, errors='replace')
    
    if p_res.returncode == 0:
        print("[G.R.D.M.] [SUCCESS] 🚀 推送完成！正在等待 GitHub Pages 刷新...")
        # 【关键】等待 30 秒让 GitHub Pages 重新构建
        time.sleep(30) 
        print("[G.R.D.M.] [INFO] GitHub Pages 应该已更新！")
    else:
        print(f"[G.R.D.M.] [ERROR] Push 失败: {p_res.stderr}")

def run_tunnel():
    print("[G.R.D.M.] [START] 正在启动 Cloudflare 隧道...")
    
    # 1. 启动隧道进程
    process = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", "http://localhost:5000"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.STDOUT, # 把错误也合并到输出里
        text=True, 
        bufsize=1
    )

    tunnel_url = None
    
    # 2. 暴力循环读取，直到抓到链接
    print("[G.R.D.M.] [WAIT] 等待隧道分配地址 (可能需要几秒)...")
    while True:
        line = process.stdout.readline()
        if not line:
            break
            
        # 【关键】不管有没有打印出来，只要行里有 trycloudflare.com 就抓！
        if "trycloudflare.com" in line:
            match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
            if match:
                tunnel_url = match.group(1)
                print(f"\n[G.R.D.M.] [FOUND] 🎉 捕获到有效链接: {tunnel_url}")
                break
        
        # 为了防止卡死，这里加个超时或者心跳检测也可以，但先试试这个
    
    if tunnel_url:
        update_index_html(tunnel_url)
        push_to_github()
        print("[G.R.D.M.] [DONE] 任务完成！Flask 和隧道将在后台继续运行。")
        # 【关键】任务完成后，让主进程退出，但保留子进程
        sys.exit(0) 
    else:
        print("[G.R.D.M.] [ERROR] 未能捕获链接，请检查 cloudflared 是否正常运行。")
        process.terminate()

if __name__ == "__main__":
    run_tunnel()

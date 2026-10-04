import subprocess
import time
import os
import re
import sys

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
    print("[G.R.D.M.] [START] 启动 Cloudflare 隧道...")
    try:
        process = subprocess.Popen(
            [TUNNEL_CMD, "tunnel", "--url", "http://localhost:5000"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, universal_newlines=True,
            encoding='utf-8', errors='replace'
        )

        tunnel_url = None
        for line in process.stdout:
            print(line, end='')
            if "trycloudflare.com" in line and "https://" in line:
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                if match:
                    tunnel_url = match.group(1)
                    print(f"\n[G.R.D.M.] [FOUND] 捕获链接: {tunnel_url}")
                    break
        
        if tunnel_url:
            update_index_html(tunnel_url)
            push_to_github()
        
        process.wait()
    except KeyboardInterrupt:
        print("\n[G.R.D.M.] [STOP] 正在关闭...")
        process.terminate()

if __name__ == "__main__":
    run_tunnel()

import subprocess
import time
import os
import re
import sys
import locale

# --- 配置区域 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
TUNNEL_CMD = "cloudflared" 
REPO_URL = "https://github.com/MessyFlowerpot/GRDMReport.git" 

def get_token():
    """安全获取 Token"""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[G.R.D.M.] [ERROR] 未找到环境变量 GITHUB_TOKEN！请先设置环境变量。")
        sys.exit(1)
    return token.strip()

def update_index_html(tunnel_url):
    """更新 index.html 中的隧道链接"""
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
            print(f"[G.R.D.M.] [DONE] 本地 index.html 坐标已更新！")
            return True
        else:
            print(f"[G.R.D.M.] [INFO] 链接未变化，跳过更新。")
            return False
            
    except Exception as e:
        print(f"[G.R.D.M.] [ERROR] 更新 HTML 失败: {e}")
        return False

def run_command(cmd, cwd=None):
    """
    【核心修复】万能命令执行器
    强制处理编码问题，防止 Windows 下 GBK/UTF-8 冲突导致崩溃
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            # 关键：指定 errors='replace'，遇到无法识别的字符（如乱码）用 ? 代替，而不是崩溃
            encoding='utf-8', 
            errors='replace' 
        )
        return result
    except Exception as e:
        # 如果 utf-8 彻底不行，尝试系统默认编码
        try:
             result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors='replace')
             return result
        except:
             return None

def push_to_github():
    """推送代码到 GitHub"""
    token = get_token()
    
    # 构建带认证的 URL
    auth_url = f"https://{token}@github.com/MessyFlowerpot/GRDMReport.git"

    print("[G.R.D.M.] [INFO] 正在将最新坐标同步至 GitHub Pages...")

    # 1. git add
    run_command(["git", "add", "."], cwd=BASE_DIR)
    
    # 2. git commit (只有有变动才提交)
    diff_res = run_command(["git", "diff", "--cached", "--quiet"], cwd=BASE_DIR)
    
    if diff_res and diff_res.returncode != 0: # 有变动
        commit_msg = f"Auto-Update Tunnel: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        c_res = run_command(["git", "commit", "-m", commit_msg], cwd=BASE_DIR)
        
        if c_res and c_res.returncode == 0:
            print("[G.R.D.M.] [DONE] Git 提交成功")
        else:
            err_msg = c_res.stderr if c_res else "Unknown Error"
            print(f"[G.R.D.M.] [ERROR] Git 提交失败: {err_msg}")
            return
    else:
        print("[G.R.D.M.] [INFO] 没有新变动，跳过提交。")

    # 3. git push
    p_res = run_command(["git", "push", auth_url, "main"], cwd=BASE_DIR)

    if p_res and p_res.returncode == 0:
        print("[G.R.D.M.] [SUCCESS] 🚀 GitHub Pages 同步完成！新世界的大门已打开！")
    else:
        print("[G.R.D.M.] [ERROR] Git Push 失败！")
        # 【核心修复】防止 err 为 None 导致的二次崩溃
        err_msg = p_res.stderr if p_res else "进程启动失败或编码严重错误"
        
        # 打印真正的错误原因（现在不会因为乱码而卡住了）
        print(f"[G.R.D.M.] [DEBUG] {err_msg}")
        
        if "https://https://" in err_msg:
             print("[G.R.D.M.] [HINT] 检测到双重 https://，请检查 Token。")
        elif "rejected" in err_msg or "violation" in err_msg:
             print("[G.R.D.M.] [HINT] 可能是 Token 过期或被 GitHub 拦截（如包含敏感信息）。")

def run_tunnel():
    """启动 Cloudflare 隧道并监听输出"""
    print("[G.R.D.M.] [WAIT] 正在启动 Cloudflare 隧道...")
    
    try:
        process = subprocess.Popen(
            [TUNNEL_CMD, "tunnel", "--url", "http://localhost:5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8', # 尝试指定 UTF-8
            errors='replace'   # 遇到乱码不崩溃
        )

        tunnel_url = None
        
        for line in process.stdout:
            print(line, end='') 
            
            if "trycloudflare.com" in line and "https://" in line:
                match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
                if match:
                    tunnel_url = match.group(1)
                    print(f"\n[G.R.D.M.] [DONE] 捕获到新隧道链接: {tunnel_url}")
                    break
        
        if tunnel_url:
            update_index_html(tunnel_url)
            push_to_github()
        else:
            print("[G.R.D.M.] [ERROR] 未能捕获到隧道链接。")

        process.wait()

    except FileNotFoundError:
        print("[G.R.D.M.] [ERROR] 找不到 cloudflared 程序！")
    except KeyboardInterrupt:
        print("\n[G.R.D.M.] [STOP] 收到停止信号，正在关闭...")
        if 'process' in locals():
            process.terminate()

if __name__ == "__main__":
    run_tunnel()

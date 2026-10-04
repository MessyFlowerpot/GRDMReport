import subprocess
import time
import os
import re
import sys
import platform

# --- 配置区域 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "index.html")
APP_PATH = os.path.join(BASE_DIR, "app.py")
TUNNEL_CMD = "cloudflared"
REPO_URL = "https://github.com/MessyFlowerpot/GRDMReport.git"

# Windows 下隐藏子进程控制台窗口的标志
_CREATE_NO_WINDOW = 0x08000000


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
    万能命令执行器
    强制处理编码问题，防止 Windows 下 GBK/UTF-8 冲突导致崩溃
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result
    except Exception as e:
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

    if diff_res and diff_res.returncode != 0:  # 有变动
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
        print("[G.R.D.M.] [SUCCESS] GitHub Pages 同步完成！新世界的大门已打开！")
    else:
        print("[G.R.D.M.] [ERROR] Git Push 失败！")
        err_msg = p_res.stderr if p_res else "进程启动失败或编码严重错误"
        print(f"[G.R.D.M.] [DEBUG] {err_msg}")

        if "https://https://" in err_msg:
            print("[G.R.D.M.] [HINT] 检测到双重 https://，请检查 Token。")
        elif "rejected" in err_msg or "violation" in err_msg:
            print("[G.R.D.M.] [HINT] 可能是 Token 过期或被 GitHub 拦截（如包含敏感信息）。")


def start_flask_app():
    """启动 Flask 应用 (app.py) 作为后台进程（不弹新终端窗口）"""
    if not os.path.exists(APP_PATH):
        print(f"[G.R.D.M.] [ERROR] 找不到 app.py！请确保 app.py 与本脚本在同一目录下。")
        return None

    print("[G.R.D.M.] [START] 正在启动 Flask 情报接收服务器 (app.py)...")
    try:
        # 关键修复：creationflags 隐藏 Windows 下的新控制台窗口
        kwargs = {
            "cwd": BASE_DIR,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
            "universal_newlines": True,
            "encoding": 'utf-8',
            "errors": 'replace',
        }
        # Windows 下隐藏子进程控制台
        if platform.system() == "Windows":
            kwargs["creationflags"] = _CREATE_NO_WINDOW

        process = subprocess.Popen(
            [sys.executable, "app.py"],
            **kwargs
        )
        # 等 Flask 启动起来（最多等5秒）
        for i in range(50):
            time.sleep(0.1)
            if process.poll() is None:
                # 进程还在跑，说明启动成功了
                print("[G.R.D.M.] [DONE] Flask 服务器已启动！")
                return process
        # 如果进程已经退出了，说明启动失败
        stdout, _ = process.communicate()
        print(f"[G.R.D.M.] [ERROR] Flask 服务器启动失败，输出: {stdout}")
        return None
    except Exception as e:
        print(f"[G.R.D.M.] [ERROR] 启动 Flask 服务器失败: {e}")
        return None


def run_tunnel():
    """启动 Flask 应用 + Cloudflare 隧道并监听输出"""
    # 先启动 Flask 应用（不弹新终端）
    flask_process = start_flask_app()
    if flask_process is None:
        print("[G.R.D.M.] [ERROR] Flask 服务器启动失败，无法继续。")
        sys.exit(1)

    print("[G.R.D.M.] [WAIT] 正在启动 Cloudflare 隧道...")

    tunnel_process = None
    try:
        tunnel_process = subprocess.Popen(
            [TUNNEL_CMD, "tunnel", "--url", "http://localhost:5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace'
        )

        tunnel_url = None

        for line in tunnel_process.stdout:
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

    except FileNotFoundError:
        print("[G.R.D.M.] [ERROR] 找不到 cloudflared 程序！")
    except KeyboardInterrupt:
        print("\n[G.R.D.M.] [STOP] 收到停止信号，正在关闭所有服务...")
        # Ctrl+C 时清理进程
        if tunnel_process is not None and tunnel_process.poll() is None:
            tunnel_process.terminate()
        if flask_process is not None and flask_process.poll() is None:
            flask_process.terminate()
        print("[G.R.D.M.] [DONE] 所有服务已关闭。")
        sys.exit(0)

    # 隧道日志读完（或捕获到URL后停止读取），不再阻塞
    # 推完就退出，让 Flask 和隧道继续在后台跑
    print("[G.R.D.M.] [DONE] 所有操作完成！")
    print("[G.R.D.M.] [INFO] Flask 服务器和隧道已在后台运行中。")
    print("[G.R.D.M.] [INFO] 如需停止服务，请关闭此终端或按 Ctrl+C。")
    sys.exit(0)


if __name__ == "__main__":
    run_tunnel()

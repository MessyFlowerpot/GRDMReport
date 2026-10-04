@echo off
chcp 65001 >nul
title G.R.D.M. 一键启动控制台

:: 1. 强制清理上次可能残留的僵尸 Python 进程（防止端口冲突）
echo [G.R.D.M.] 正在清理可能残留的旧进程...
taskkill /F /IM python.exe >nul 2>&1

:: 2. 后台静默启动 app.py (接待员)
echo [G.R.D.M.] 正在启动 Flask 服务器 (app.py)...
start "" /B "C:\Users\Hello\AppData\Local\Python\pythoncore-3.14-64\python.exe" "app.py"

:: 等待 2 秒，给 Flask 一点启动时间
echo [G.R.D.M.] 等待服务器就绪...
timeout /t 2 /nobreak >nul

:: 3. 在当前窗口启动 GRDM_Manager.py (后勤部长)
echo [G.R.D.M.] 正在启动隧道管理器 (GRDM_Manager.py)...
echo ==========================================
"C:\Users\Hello\AppData\Local\Python\pythoncore-3.14-64\python.exe" "GRDM_Manager.py"

:: 4. 运行结束后暂停，方便你查看结果
echo ==========================================
echo [G.R.D.M.] 脚本运行结束。
pause
@echo off
rem ============================================================
rem  B站明星人脸识别 - 本地服务一键启动 (Windows)
rem  首次运行自动创建虚拟环境并安装依赖
rem  注意: 本文件为 GBK 编码, 请勿另存为 UTF-8
rem ============================================================
setlocal
cd /d "%~dp0.."
set VENV_DIR=.venv

echo ============================================================
echo   B站明星人脸识别 - 本地识别服务
echo ============================================================

rem ---- 0. 检查端口是否已被占用（避免重复启动报错）----
netstat -ano | findstr ":5000" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo.
    echo [提示] 5000 端口已被占用，识别服务可能已经在运行。
    echo        浏览器访问 http://127.0.0.1:5000/health 可确认。
    echo        若需重启，请先关闭占用该端口的进程后重新运行本脚本。
    echo.
    pause
    goto :eof
)

rem ---- 1. 虚拟环境 ----
if exist "%VENV_DIR%\Scripts\python.exe" (
    echo [1/3] 虚拟环境已存在
) else (
    echo [1/3] 正在创建虚拟环境 .venv ...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo       创建失败，请确认已安装 Python 3.8+ 并勾选 Add to PATH。
        goto :err
    )
)

rem ---- 2. 依赖 ----
echo [2/3] 检查并安装依赖（首次运行需数分钟，请耐心等待）...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo       依赖安装失败，请检查网络连接或改用国内镜像源。
    goto :err
)

rem ---- 3. 启动服务 ----
echo [3/3] 启动识别服务：http://127.0.0.1:5000
echo       首次加载 InsightFace 模型约需 10-30 秒。
echo       看到 "Running on http://127.0.0.1:5000" 即启动成功。
echo       按 Ctrl+C 可停止服务。
echo.
"%VENV_DIR%\Scripts\python.exe" app.py
if errorlevel 1 goto :err
goto :eof

:err
echo.
echo 启动失败，请检查上方错误信息。
pause

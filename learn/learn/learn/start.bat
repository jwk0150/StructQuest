@echo off
chcp 65001 >nul
echo ========================================
echo   StructQuest 一键启动脚本（SQLite 模式）
echo ========================================
echo.
echo 数据库使用 SQLite，无需额外安装数据库服务。
echo.
echo [1] 启动后端 (Port 8008) + 前端 (Port 5173)
echo [2] 仅启动后端 (Port 8008)
echo [3] 仅启动前端 (Port 5173)
echo [4] 退出
echo.

set /p choice="请选择启动方式 (1/2/3/4): "

if "%choice%"=="1" goto run_both
if "%choice%"=="2" goto run_backend
if "%choice%"=="3" goto run_frontend
if "%choice%"=="4" goto end
goto end

:run_both
echo.
echo 正在检查 Redis...
tasklist /fi "imagename eq redis-server.exe" 2>nul | find /i "redis-server.exe" >nul
if errorlevel 1 (
    echo 正在启动 Redis...
    start "Redis" /min "d:\lastone\Redis-x64-5.0.14.1\redis-server.exe"
    timeout /t 2 /nobreak >nul
    echo Redis 启动完成
) else (
    echo Redis 已在运行
)
echo.
echo 正在启动后端 (Port 8008)...
start "StructQuest-Backend" cmd /k "chcp 65001 >nul & cd /d "%~dp0struct-quest-backend" && .\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload"

timeout /t 3 /nobreak >nul

echo 正在启动前端 (Port 5173)...
start "StructQuest-Frontend" cmd /k "chcp 65001 >nul & cd /d "%~dp0struct-quest-frontend" && npx vite --port 5173 --host"

echo.
echo ========================================
echo   启动完成！
echo   前端: http://localhost:5173
echo   后端: http://localhost:8008
echo   健康检查: http://localhost:8008/api/health
echo ========================================
goto end

:run_backend
echo.
echo 正在检查 Redis...
tasklist /fi "imagename eq redis-server.exe" 2>nul | find /i "redis-server.exe" >nul
if errorlevel 1 (
    echo 正在启动 Redis...
    start "Redis" /min "d:\lastone\Redis-x64-5.0.14.1\redis-server.exe"
    timeout /t 2 /nobreak >nul
    echo Redis 启动完成
) else (
    echo Redis 已在运行
)
echo.
echo 正在启动后端 (Port 8008)...
start "StructQuest-Backend" cmd /k "chcp 65001 >nul & cd /d "%~dp0struct-quest-backend" && .\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8008 --reload"
echo 后端启动命令已下发 (Port 8008)
goto end

:run_frontend
echo.
echo 正在启动前端 (Port 5173)...
start "StructQuest-Frontend" cmd /k "chcp 65001 >nul & cd /d "%~dp0struct-quest-frontend" && npx vite --port 5173 --host"
echo 前端启动命令已下发 (Port 5173)
goto end

:end
echo.
pause

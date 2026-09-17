@echo off
setlocal
if "%1"=="down" goto down
if "%1"=="logs" goto logs

echo 正在启动中文彩票数据分析网页……
docker compose up --build
exit /b %errorlevel%

:down
docker compose down
exit /b %errorlevel%

:logs
docker compose logs -f
exit /b %errorlevel%

@echo off
chcp 65001 >nul
title ERP-Stop-All
echo Stopping all ERP/FDE services ...
for %%P in (8000 8001 5173 5174) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
    echo   stop port %%P (PID %%a)
    taskkill /PID %%a /F >nul 2>&1
  )
)
echo All services stopped.
ping -n 4 127.0.0.1 >nul


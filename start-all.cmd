@echo off
chcp 65001 >nul
title ERP-All-Services
cd /d D:\erp

REM stop old services first
for %%P in (8000 8001 5173 5174) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
  )
)
timeout /t 2 >nul

echo [1/4] Starting ERP Backend :8000 ...
start "ERP-Backend :8000" cmd /k "cd /d D:\erp\erp-backend && C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info"

echo [2/4] Starting FDE Risk Agent :8001 ...
start "FDE-Agents :8001" cmd /k "cd /d D:\erp\fde-agents && C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info"

echo [3/4] Starting ERP Web :5173 ...
start "ERP-Web :5173" cmd /k "cd /d D:\erp\erp-web && npm run dev"

echo [4/4] Starting FDE Web :5174 ...
start "FDE-Web :5174" cmd /k "cd /d D:\erp\fde-web && npm run dev"

echo.
echo ============================================
echo  All services started.
echo  ERP Web : http://localhost:5173
echo  FDE Web : http://localhost:5174
echo  ERP API : http://localhost:8000/docs
echo  FDE API : http://localhost:8001/docs
echo ============================================
ping -n 6 127.0.0.1 >nul


@echo off
setlocal

REM --- Cập nhật: Tự động xác định đường dẫn gốc của dự án ---
REM %~dp0 sẽ lấy đường dẫn của thư mục chứa file .bat này.
REM Bằng cách này, bạn có thể đặt file .bat này vào bất kỳ đâu 
REM cùng với các thư mục backend, frontend... và nó sẽ luôn chạy đúng.
set "PROJECT_ROOT=%~dp0"

REM --- Cài đặt tiêu đề cho cửa sổ terminal chính ---
TITLE Project Starter - An Ninh Noi Bo (Production Mode)

REM --- Hướng dẫn ---
echo.
echo ====================================================================
echo  Dang khoi chay 3 services cho du an An Ninh Noi Bo...
echo.
echo  Duong dan du an duoc phat hien: %PROJECT_ROOT%
echo.
echo  [CHE DO PRODUCTION] - Tu dong khoi dong lai khi co loi
echo  - Backend Chinh (Port 8000)
echo  - Service Quet CCCD (Port 5009)
echo.
echo  [CHE DO DEVELOPMENT]
echo  - Frontend (Giao dien nguoi dung)
echo.
echo  Luu y: De dung hoan toan he thong, ban can dong ca 3 cua so.
echo ====================================================================
echo.

REM --- Lệnh 1: Khởi chạy Backend Chính (Port 8000) ---
echo Khoi chay Backend Chinh (Production Mode)...
start "Backend - Port 8000 (Production)" cmd /c "cd /d "%PROJECT_ROOT%backend" && call .\.venv\Scripts\activate.bat && (for /l %%x in (1,1,1) do (echo Starting server... && uvicorn app.main:app --host 0.0.0.0 --port 8000 && echo Server stopped. Restarting in 5s... && timeout /t 5))"

REM --- Lệnh 2: Khởi chạy Service Quét CCCD (Port 5009) ---
echo Khoi chay ID Card Service (Production Mode)...
start "ID Card Service - Port 5009 (Production)" cmd /c "cd /d "%PROJECT_ROOT%id_card_extractor_service" && call .\.venv\Scripts\activate.bat && (for /l %%x in (1,1,1) do (echo Starting ID service... && uvicorn main:app --host 0.0.0.0 --port 5009 && echo ID service stopped. Restarting in 5s... && timeout /t 5))"

REM --- Lệnh 3: Khởi chạy Frontend (Development Mode) ---
echo Khoi chay Frontend (Development Mode)...
start "Frontend" cmd /k "cd /d "%PROJECT_ROOT%frontend" && npm run dev"

echo.
echo Khoi chay hoan tat. Vui long kiem tra 3 cua so terminal moi.

REM Tạm dừng để người dùng đọc thông báo
pause


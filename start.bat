@echo off
echo ============================================
echo Emergency Department Simulation Server
echo ============================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting server...
echo.
python app.py
pause

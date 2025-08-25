@echo off
echo 🚀 Starting LeadFlow Scraper Service...
echo 📍 API will be available at: http://localhost:3002
echo 📚 API Documentation: http://localhost:3002/docs
echo 🔧 Debug mode: ENABLED
echo 🔄 Auto-reload: ENABLED
echo ==================================================

:: Activate virtual environment
call .venv\Scripts\activate.bat

:: Run the application
python run.py

pause

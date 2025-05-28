@echo off
echo Starting Streamlit UI...
cd /d D:\Study\AILearning\shared_Environment\Scripts
call activate.bat
cd /d D:\Study\AILearning\MLProjects\creditcardfrauddetection
streamlit run ui\app.py
pause

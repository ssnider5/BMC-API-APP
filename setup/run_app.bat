@echo off

cd /d "%~dp0"

if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate.bat

pip install --no-user -r requirements.txt

python main.pyw

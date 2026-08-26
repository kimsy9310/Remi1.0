@echo off
cd /d "%~dp0"
REM streamlit.exe 는 설치돼 있어도 PATH 에 없는 경우가 많다.
REM python -m 으로 부르면 PATH 와 무관하게 동작한다.
python -m streamlit run app\main.py
pause

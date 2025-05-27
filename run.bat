@echo off
echo Doc Translator 시작 중...

:: Python 가상환경 활성화 (필요시 주석 해제)
:: call .venv\Scripts\activate

:: 필요한 의존성 설치
echo 필요한 패키지 설치 중...
pip install -r requirements.txt

:: 애플리케이션 실행
echo 애플리케이션을 시작합니다...
python app.py

:: 일시 정지 (오류 발생 시 창이 닫히는 것 방지)
pause

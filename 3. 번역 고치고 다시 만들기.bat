@echo off
title Odd Realm 한글패치 - 다시 만들기
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto nopython

cd "tool"
echo [1/3] 필요한 파이썬 꾸러미를 확인합니다...
python -m pip install -r requirements.txt --disable-pip-version-check --quiet
if errorlevel 1 goto fail

echo.
echo [2/3] 게임에서 원본 파일을 가져옵니다...
python "1_원본가져오기.py"
if errorlevel 1 goto fail

echo.
echo [3/3] 전체를 다시 만듭니다. 30초쯤 걸립니다...
python "2_빌드.py"
if errorlevel 1 goto fail

echo.
echo 새로 만든 파일을 "배포" 폴더로 옮깁니다...
copy /Y "out\dist\*.exe" "..\배포\" >nul 2>nul
copy /Y "out\dist\*.zip" "..\배포\" >nul 2>nul

echo.
echo ============================================================
echo  완료되었습니다.
echo  "배포" 폴더의 파일이 최신으로 바뀌었습니다.
echo ============================================================
pause
exit /b 0

:nopython
echo.
echo  Python 이 설치되어 있지 않습니다.
echo.
echo  https://www.python.org/downloads/ 에서 내려받아 설치해 주세요.
echo  설치 화면에서 "Add Python to PATH" 를 꼭 체크하셔야 합니다.
echo.
pause
exit /b 1

:fail
echo.
echo  중간에 실패했습니다. 위에 나온 메시지를 확인해 주세요.
echo.
pause
exit /b 1

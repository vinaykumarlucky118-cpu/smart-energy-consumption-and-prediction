@echo off
title Push Smart Energy to GitHub
color 0A
echo ==========================================================
echo  Pushing Smart Energy to GitHub
echo  Repository: https://github.com/vinaykumarlucky118-cpu/smartenergy
echo ==========================================================
echo.

set "PATH=C:\Users\vinay\AppData\Local\Microsoft\WinGet\Packages\Git.MinGit_Microsoft.Winget.Source_8wekyb3d8bbwe\cmd;C:\Users\vinay\AppData\Local\Programs\Git Credential Manager;C:\Users\vinay\AppData\Local\Microsoft\WinGet\Packages\GitHub.cli_Microsoft.Winget.Source_8wekyb3d8bbwe\bin;%PATH%"

echo Pushing commits to GitHub (Git Credential Manager will open browser sign-in if needed)...
git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ==========================================================
    echo  SUCCESS! Your project is now live on GitHub:
    echo  https://github.com/vinaykumarlucky118-cpu/smartenergy
    echo ==========================================================
) else (
    echo.
    echo If push was not completed, please try again or check credentials.
)
echo.
pause

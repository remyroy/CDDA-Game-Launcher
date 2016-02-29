@echo off
echo Updating CDDA Game Launcher
rem Update batch file. %~1 is parent pid, %~2 is path to update, %~3 is path to update directory, %~4 is path to current and %~5 is path to current directory

rem Wait for parent to exit
:waitforpid
tasklist /fi "pid eq %~1" 2>nul | find "%~1" >nul
if %ERRORLEVEL%==0 (
  timeout /t 1 /nobreak >nul
  goto :waitforpid
)

rem Delete current executable
:retrydel
del /F "%~4" >nul 2>&1
if exist "%~4" (
  timeout /t 1 /nobreak >nul
  goto :retrydel
)

rem Move update to current directory
move /Y "%~2" "%~5" >nul

rem Launch updated executable
start "" "%~4"

rem Delete update directory
(goto) 2>nul & rmdir /S /Q "%~3" & exit
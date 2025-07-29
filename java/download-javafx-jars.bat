@echo off
echo Downloading JavaFX JARs for runtime...

rem Create directory for JavaFX JARs
if not exist "javafx-jars" mkdir javafx-jars

rem Download JavaFX SDK (contains JARs)
echo Downloading JavaFX SDK...
curl -L -o javafx-21-windows.zip https://download2.gluonhq.com/openjfx/21/openjfx-21_windows-x64_bin-sdk.zip

echo Extracting JavaFX SDK...
powershell -command "Expand-Archive -Path 'javafx-21-windows.zip' -DestinationPath '.' -Force"

rem Move JAR files to javafx-jars directory
echo Moving JAR files...
if exist javafx-sdk-21 (
    move javafx-sdk-21\lib\*.jar javafx-jars\
    echo Moving native libraries...
    xcopy /s /y javafx-sdk-21\bin\*.dll javafx-jars\
    rmdir /s /q javafx-sdk-21
) else (
    echo ERROR: Failed to extract JavaFX SDK
    pause
    exit /b 1
)

del javafx-21-windows.zip

echo JavaFX JARs downloaded successfully to javafx-jars directory!
pause
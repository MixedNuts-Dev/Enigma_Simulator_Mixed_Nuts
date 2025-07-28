@echo off
echo Building Bombe Simulator EXE (without Maven)...

rem Check JAVA_HOME
if not defined JAVA_HOME (
    echo ERROR: JAVA_HOME is not set. Please set JAVA_HOME to your JDK 21 installation directory.
    echo Example: set JAVA_HOME=C:\Program Files\Java\jdk-21
    pause
    exit /b 1
)

echo Using JAVA_HOME: %JAVA_HOME%

rem Check if JAR exists
if not exist target\enigma-simulator-1.0.0.jar (
    echo ERROR: JAR file not found. Please build the project first.
    pause
    exit /b 1
)

rem Create dist directory
if exist dist-bombe rmdir /s /q dist-bombe
mkdir dist-bombe

rem Create exe file with jpackage
echo Creating Bombe EXE with jpackage...
echo.
echo NOTE: This will create an installer. For a portable app, use create-portable-exe.bat instead.
echo.
echo Checking for WiX Toolset...
where candle.exe >nul 2>&1
if errorlevel 1 (
    echo WARNING: WiX Toolset not found. Please install it from https://wixtoolset.org/
    echo Creating MSI installer instead of EXE...
    set INSTALLER_TYPE=msi
) else (
    set INSTALLER_TYPE=exe
)

jpackage ^
    --type %INSTALLER_TYPE% ^
    --name "Bombe Simulator Java" ^
    --app-version 1.0.0 ^
    --vendor "Enigma Project" ^
    --description "Bombe Attack Simulator for Enigma Machine" ^
    --input target ^
    --main-jar enigma-simulator-1.0.0.jar ^
    --main-class com.enigma.gui.BombeGUI ^
    --dest dist-bombe ^
    --module-path "javafx-runtime" ^
    --add-modules javafx.controls,javafx.fxml ^
    --java-options "-Dfile.encoding=UTF-8" ^
    --java-options "-Xmx512m" ^
    --win-menu ^
    --win-shortcut ^
    --win-dir-chooser

echo.
echo Build complete! Check the dist-bombe directory for the installer.
pause
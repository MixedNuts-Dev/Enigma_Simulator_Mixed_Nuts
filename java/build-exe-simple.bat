@echo off
echo Building Enigma Simulator EXE (Simple method without JavaFX modules)...

rem Check if JAR with dependencies exists
if not exist target\enigma-simulator-1.0.0-jar-with-dependencies.jar (
    echo ERROR: JAR file not found. Please build the project first using: mvn clean package
    pause
    exit /b 1
)

rem Create dist directory
if exist dist rmdir /s /q dist
mkdir dist

echo Creating EXE with jpackage using fat JAR...

jpackage ^
    --type app-image ^
    --name "Enigma Simulator" ^
    --app-version 1.0.0 ^
    --vendor "Enigma Project" ^
    --description "Enigma Machine Simulator with Bombe Attack" ^
    --input target ^
    --main-jar enigma-simulator-1.0.0-jar-with-dependencies.jar ^
    --main-class com.enigma.gui.EnigmaGUI ^
    --dest dist ^
    --java-options "-Dfile.encoding=UTF-8" ^
    --java-options "-Xmx512m" ^
    --icon icon.ico

echo.
echo Build complete! 
echo Executable location: dist\Enigma Simulator\Enigma Simulator.exe
echo.
echo You can also run directly with: run-enigma.bat
pause
@echo off
echo ========================================
echo Enigma Simulator C++ - Console Version
echo ========================================
echo.

REM Parse command line arguments
set BUILD_INSTALLER=0
if "%1"=="--installer" set BUILD_INSTALLER=1

REM Clean build directory for fresh build
echo [1/4] Cleaning previous build...
if exist build_console (
    rmdir /s /q build_console
    echo Previous build directory removed.
)

echo.
echo [2/4] Creating build directory...
mkdir build_console
cd build_console

echo.
echo [3/4] Configuring with CMake...
cmake -G "Visual Studio 17 2022" -A x64 ..

if errorlevel 1 (
    echo ERROR: CMake configuration failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo [4/4] Building Release version...
cmake --build . --config Release

if errorlevel 1 (
    echo ERROR: Build failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build successful!
echo Executable: build_console\Release\EnigmaSimulatorCpp.exe
echo ========================================

REM Create installer if requested
if %BUILD_INSTALLER%==1 (
    echo.
    echo Creating installer...
    
    REM Check for NSIS
    where makensis >nul 2>&1
    if errorlevel 1 (
        echo.
        echo Creating ZIP package instead (NSIS not found)...
        
        cd Release
        powershell -Command "Compress-Archive -Path EnigmaSimulatorCpp.exe -DestinationPath ..\..\EnigmaSimulatorCpp_Console_v1.0.zip -Force"
        cd ..
        
        echo ZIP package created: EnigmaSimulatorCpp_Console_v1.0.zip
    ) else (
        REM Use CPack to create installer
        cpack -G NSIS -C Release
        
        if errorlevel 1 (
            echo WARNING: CPack failed, creating ZIP instead...
            cd Release
            powershell -Command "Compress-Archive -Path EnigmaSimulatorCpp.exe -DestinationPath ..\..\EnigmaSimulatorCpp_Console_v1.0.zip -Force"
            cd ..
            echo ZIP package created: EnigmaSimulatorCpp_Console_v1.0.zip
        ) else (
            echo Installer created: build_console\Enigma Simulator Cpp-1.0.0-win64.exe
        )
    )
)

cd ..
echo.
echo Done! To create an installer, run: build_console.bat --installer
echo.
pause
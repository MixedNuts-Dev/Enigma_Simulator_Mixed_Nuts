@echo off
echo Building Enigma Simulator C++...
echo.

REM Clean build directory for fresh build
echo Cleaning previous build...
if exist build (
    rmdir /s /q build
    echo Previous build directory removed.
)

echo Creating fresh build directory...
mkdir build
cd build

echo.
echo Configuring with CMake...
cmake -G "Visual Studio 17 2022" -A x64 ..

if errorlevel 1 (
    echo ERROR: CMake configuration failed!
    pause
    exit /b 1
)

echo.
echo Building Release version...
cmake --build . --config Release

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Build successful!
echo Executable: build\Release\EnigmaSimulatorCpp.exe
echo.
echo To create an installer, run: build_installer.bat
echo.
pause
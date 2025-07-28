@echo off
echo ========================================
echo Enigma Simulator C++ - GUI Version
echo ========================================
echo.

REM Parse command line arguments
set BUILD_INSTALLER=0
if "%1"=="--installer" set BUILD_INSTALLER=1

REM Check for Qt6
echo [1/5] Checking for Qt6...
set QT6_FOUND=0
set QT6_PATH=

REM Check common Qt6 installation paths
if exist "C:\Qt\6.9.1\msvc2022_64" (
    set QT6_PATH=C:\Qt\6.9.1\msvc2022_64
    set QT6_FOUND=1
) else if exist "C:\Qt\6.5.0\msvc2019_64" (
    set QT6_PATH=C:\Qt\6.5.0\msvc2019_64
    set QT6_FOUND=1
) else if exist "C:\Qt\6.4.0\msvc2019_64" (
    set QT6_PATH=C:\Qt\6.4.0\msvc2019_64
    set QT6_FOUND=1
)

if %QT6_FOUND%==0 (
    echo ERROR: Qt6 not found!
    echo.
    echo Please install Qt6 from https://www.qt.io/download
    echo Or use build_console.bat for console-only version.
    echo.
    echo Checked paths:
    echo - C:\Qt\6.9.1\msvc2022_64
    echo - C:\Qt\6.5.0\msvc2019_64
    echo - C:\Qt\6.4.0\msvc2019_64
    pause
    exit /b 1
)

echo Qt6 found at: %QT6_PATH%

REM Clean build directory
echo.
echo [2/5] Cleaning previous build...
if exist build_gui (
    rmdir /s /q build_gui
    echo Previous build directory removed.
)

echo.
echo [3/5] Creating build directory...
mkdir build_gui
cd build_gui

echo.
echo [4/5] Configuring with CMake (Qt6 enabled)...
cmake -G "Visual Studio 17 2022" -A x64 ^
    -DCMAKE_PREFIX_PATH="%QT6_PATH%" ^
    -DQt6_DIR="%QT6_PATH%\lib\cmake\Qt6" ..

if errorlevel 1 (
    echo ERROR: CMake configuration failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo [5/5] Building Release version...
cmake --build . --config Release

if errorlevel 1 (
    echo ERROR: Build failed!
    cd ..
    pause
    exit /b 1
)

echo.
echo Deploying Qt dependencies...
"%QT6_PATH%\bin\windeployqt.exe" Release\EnigmaSimulatorCppGUI.exe

echo.
echo ========================================
echo Build successful!
echo Console: build_gui\Release\EnigmaSimulatorCpp.exe
echo GUI:     build_gui\Release\EnigmaSimulatorCppGUI.exe
echo ========================================

REM Create installer if requested
if %BUILD_INSTALLER%==1 (
    echo.
    echo Creating installer package...
    
    REM Create distribution directory
    if exist ..\dist_gui rmdir /s /q ..\dist_gui
    mkdir ..\dist_gui
    
    REM Copy executables and Qt dependencies
    xcopy /Y /E /I Release\*.* ..\dist_gui\
    
    REM Check for NSIS
    where makensis >nul 2>&1
    if errorlevel 1 (
        echo.
        echo Creating ZIP package (NSIS not found)...
        
        cd ..
        powershell -Command "Compress-Archive -Path dist_gui\* -DestinationPath EnigmaSimulatorCpp_GUI_v1.0.zip -Force"
        rmdir /s /q dist_gui
        
        echo ZIP package created: EnigmaSimulatorCpp_GUI_v1.0.zip
    ) else (
        echo Creating NSIS installer...
        cd ..
        
        REM Create NSIS script
        (
echo !define PRODUCT_NAME "Enigma Simulator C++ GUI"
echo !define PRODUCT_VERSION "1.0.0"
echo !define PRODUCT_PUBLISHER "MixedNuts tukasa"
echo.
echo Name "${PRODUCT_NAME}"
echo OutFile "EnigmaSimulatorCpp_GUI_Setup.exe"
echo InstallDir "$PROGRAMFILES64\Enigma Simulator Cpp"
echo RequestExecutionLevel admin
echo.
echo !include "MUI2.nsh"
echo !insertmacro MUI_PAGE_WELCOME
echo !insertmacro MUI_PAGE_DIRECTORY
echo !insertmacro MUI_PAGE_INSTFILES
echo !insertmacro MUI_PAGE_FINISH
echo !insertmacro MUI_UNPAGE_WELCOME
echo !insertmacro MUI_UNPAGE_CONFIRM
echo !insertmacro MUI_UNPAGE_INSTFILES
echo !insertmacro MUI_LANGUAGE "English"
echo.
echo Section "Main"
echo     SetOutPath $INSTDIR
echo     File /r "dist_gui\*.*"
echo.
echo     CreateDirectory "$SMPROGRAMS\Enigma Simulator C++"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Enigma Console.lnk" "$INSTDIR\EnigmaSimulatorCpp.exe"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Enigma GUI.lnk" "$INSTDIR\EnigmaSimulatorCppGUI.exe"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Uninstall.lnk" "$INSTDIR\uninstall.exe"
echo     CreateShortcut "$DESKTOP\Enigma Simulator C++ GUI.lnk" "$INSTDIR\EnigmaSimulatorCppGUI.exe"
echo.
echo     WriteUninstaller "$INSTDIR\uninstall.exe"
echo.
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCppGUI" "DisplayName" "${PRODUCT_NAME}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCppGUI" "UninstallString" "$INSTDIR\uninstall.exe"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCppGUI" "Publisher" "${PRODUCT_PUBLISHER}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCppGUI" "DisplayVersion" "${PRODUCT_VERSION}"
echo SectionEnd
echo.
echo Section "Uninstall"
echo     Delete "$INSTDIR\*.*"
echo     RMDir /r "$INSTDIR"
echo     Delete "$SMPROGRAMS\Enigma Simulator C++\*.*"
echo     RMDir "$SMPROGRAMS\Enigma Simulator C++"
echo     Delete "$DESKTOP\Enigma Simulator C++ GUI.lnk"
echo     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCppGUI"
echo SectionEnd
        ) > gui_installer.nsi
        
        makensis gui_installer.nsi
        
        if errorlevel 1 (
            echo WARNING: NSIS failed, keeping ZIP package...
            powershell -Command "Compress-Archive -Path dist_gui\* -DestinationPath EnigmaSimulatorCpp_GUI_v1.0.zip -Force"
            echo ZIP package created: EnigmaSimulatorCpp_GUI_v1.0.zip
        ) else (
            echo Installer created: EnigmaSimulatorCpp_GUI_Setup.exe
        )
        
        REM Cleanup
        del gui_installer.nsi
        rmdir /s /q dist_gui
        cd build_gui
    )
)

cd ..
echo.
echo Done! To create an installer, run: build_gui.bat --installer
echo.
pause
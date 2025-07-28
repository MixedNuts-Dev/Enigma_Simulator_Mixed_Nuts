@echo off
echo Creating Enigma Simulator C++ GUI Installer...
echo.

REM Check if GUI build exists
if not exist build_gui\Release\EnigmaSimulatorCppGUI.exe (
    echo ERROR: GUI build not found! Please run build_with_gui.bat first.
    pause
    exit /b 1
)

REM Create installer directory
echo Preparing installer files...
if exist installer_files rmdir /s /q installer_files
mkdir installer_files

REM Copy executables
copy build_gui\Release\EnigmaSimulatorCpp.exe installer_files\
copy build_gui\Release\EnigmaSimulatorCppGUI.exe installer_files\

REM Copy Qt dependencies
echo Copying Qt dependencies...
xcopy /Y /E /I build_gui\Release\*.dll installer_files\
xcopy /Y /E /I build_gui\Release\platforms installer_files\platforms\
xcopy /Y /E /I build_gui\Release\styles installer_files\styles\
xcopy /Y /E /I build_gui\Release\imageformats installer_files\imageformats\

REM Create simple installer with NSIS
echo.
echo Creating NSIS installer script...
(
echo ; Enigma Simulator C++ GUI Installer Script
echo !define PRODUCT_NAME "Enigma Simulator C++"
echo !define PRODUCT_VERSION "1.0.0"
echo !define PRODUCT_PUBLISHER "MixedNuts tukasa"
echo.
echo Name "${PRODUCT_NAME}"
echo OutFile "EnigmaSimulatorCppSetup.exe"
echo InstallDir "$PROGRAMFILES64\Enigma Simulator Cpp"
echo.
echo ; Request admin privileges
echo RequestExecutionLevel admin
echo.
echo ; Pages
echo Page directory
echo Page instfiles
echo.
echo Section "Main Section"
echo     SetOutPath $INSTDIR
echo     File /r "installer_files\*.*"
echo.
echo     ; Create shortcuts
echo     CreateDirectory "$SMPROGRAMS\Enigma Simulator C++"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Enigma Console.lnk" "$INSTDIR\EnigmaSimulatorCpp.exe"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Enigma GUI.lnk" "$INSTDIR\EnigmaSimulatorCppGUI.exe"
echo     CreateShortcut "$SMPROGRAMS\Enigma Simulator C++\Uninstall.lnk" "$INSTDIR\uninstall.exe"
echo     CreateShortcut "$DESKTOP\Enigma Simulator C++.lnk" "$INSTDIR\EnigmaSimulatorCppGUI.exe"
echo.
echo     ; Create uninstaller
echo     WriteUninstaller "$INSTDIR\uninstall.exe"
echo.
echo     ; Registry entries
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCpp" "DisplayName" "Enigma Simulator C++"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCpp" "UninstallString" "$INSTDIR\uninstall.exe"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCpp" "Publisher" "${PRODUCT_PUBLISHER}"
echo     WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCpp" "DisplayVersion" "${PRODUCT_VERSION}"
echo SectionEnd
echo.
echo Section "Uninstall"
echo     Delete "$INSTDIR\*.*"
echo     RMDir /r "$INSTDIR"
echo     Delete "$SMPROGRAMS\Enigma Simulator C++\*.*"
echo     RMDir "$SMPROGRAMS\Enigma Simulator C++"
echo     Delete "$DESKTOP\Enigma Simulator C++.lnk"
echo     DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaSimulatorCpp"
echo SectionEnd
) > installer.nsi

echo.
echo Compiling NSIS installer...
makensis installer.nsi

if errorlevel 1 (
    echo.
    echo ERROR: NSIS compilation failed!
    echo Make sure NSIS is installed and in PATH: https://nsis.sourceforge.io/Download
    pause
    exit /b 1
)

echo.
echo Installer created successfully!
echo Location: EnigmaSimulatorCppSetup.exe
echo.

REM Cleanup
del installer.nsi
rmdir /s /q installer_files

pause
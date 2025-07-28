# Enigma Simulator C++ - ビルド手順

## ビルドオプション

### 1. コンソール版（
```cmd
# ビルドのみ
build_console.bat

# ビルド + インストーラー作成
build_console.bat --installer
```
- Qt6不要
- 軽量・高速
- コマンドライン用途

### 2. GUI版（Qt6必要）
```cmd
# ビルドのみ
build_gui.bat

# ビルド + インストーラー作成
build_gui.bat --installer
```
- Qt6が必要
- GUIアプリケーション付き
- より大きなファイルサイズ

## 必要なツール

### 基本ビルド
- Visual Studio 2022
- CMake 3.16以降

### GUI版ビルド
- Qt6 (https://www.qt.io/download)
- Qt VS Tools拡張機能（オプション）

### インストーラー作成
- NSIS (https://nsis.sourceforge.io/Download)

## トラブルシューティング

### Qt6が見つからない
- Qt6をデフォルトパス（C:\Qt\6.x.x\msvc2019_64）にインストール
- または環境変数CMAKE_PREFIX_PATHを設定

### NSISが見つからない
- NSISをインストール後、システム環境変数PATHに追加
- または直接パスを指定して実行

### ビルドエラー
- buildフォルダを手動で削除して再試行
- Visual Studio 2022がインストールされているか確認
- CMakeのバージョンを確認（cmake --version）

## 出力ファイル

### コンソール版
- 実行ファイル: `build_console\Release\EnigmaSimulatorCpp.exe`
- インストーラー/ZIP: `EnigmaSimulatorCpp_Console_v1.0.zip` または `.exe`

### GUI版
- コンソール: `build_gui\Release\EnigmaSimulatorCpp.exe`
- GUI: `build_gui\Release\EnigmaSimulatorCppGUI.exe`
- インストーラー/ZIP: `EnigmaSimulatorCpp_GUI_v1.0.zip` または `EnigmaSimulatorCpp_GUI_Setup.exe`

## 使用例

```cmd
# コンソール版をビルドしてインストーラーも作成
build_console.bat --installer

# GUI版をビルドのみ（インストーラーなし）
build_gui.bat

# GUI版をビルドしてインストーラーも作成
build_gui.bat --installer
```
# Enigma Simulator C++ - ビルド手順

## ビルドオプション

### 1. コンソール版のみ（推奨）
```cmd
build.bat
```
- Qt6不要
- 軽量・高速
- コマンドライン用途

### 2. GUI版を含むビルド
```cmd
build_with_gui.bat
```
- Qt6が必要
- GUIアプリケーション付き
- より大きなファイルサイズ

## インストーラー作成

### コンソール版インストーラー
```cmd
build.bat
build_installer.bat
```

### GUI版インストーラー
```cmd
build_with_gui.bat
build_gui_installer.bat
```

## 必要なツール

### 基本ビルド
- Visual Studio 2022
- CMake 3.16以降

### GUI版ビルド（追加）
- Qt6 (https://www.qt.io/download)
- Qt VS Tools拡張機能（オプション）

### インストーラー作成（追加）
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
- 実行ファイル: `build\Release\EnigmaSimulatorCpp.exe`
- インストーラー: `build\Enigma Simulator Cpp-1.0.0-win64.exe`

### GUI版
- コンソール: `build_gui\Release\EnigmaSimulatorCpp.exe`
- GUI: `build_gui\Release\EnigmaSimulatorCppGUI.exe`
- インストーラー: `EnigmaSimulatorCppSetup.exe`
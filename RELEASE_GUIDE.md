# Enigma Simulator - リリースガイド

## 各バージョンのリリース配布方法

### Python版
- **ファイル**: `enigma_simulator.exe`（単体実行可能）
- **配布方法**: そのままGitHub Releasesにアップロード
- **ファイルサイズ**: 約30-50MB
- **必要環境**: Windows 7以降（追加インストール不要）

### Java版
- **ファイル**: `Enigma Simulator-1.0.0.msi`
- **配布方法**: MSIインストーラーをそのままアップロード
- **ファイルサイズ**: 約50-80MB
- **必要環境**: Java 8以降（インストーラーが確認）

### C++版
- **配布形式**: ソースコードのみ
- **理由**: 高速なコンソール版として開発者向けに提供
- **ビルド方法**: CMakeを使用してローカルでビルド
- **必要環境**: Visual Studio 2022, CMake 3.16以降

## GitHub Releasesでの構成例

```
Enigma Simulator v1.0.0
├── Python/
│   └── enigma_simulator.exe
├── Java/
│   └── Enigma_Simulator-1.0.0.msi
└── Source/
    └── source_code.zip (全ソースコード含む)
```

## ビルド手順

### Python版のexeビルド
```cmd
cd python
python -m PyInstaller --onefile --noconsole --name enigma_simulator --hidden-import=src.bombe main.py
```

### Java版のMSIビルド
```cmd
cd java
mvn clean package
# その後、Visual Studio Installer Projectsでビルド
```

### C++版のビルド（開発者向け）
```cmd
cd cpp
mkdir build && cd build
cmake .. && cmake --build . --config Release
```

## 推奨事項

1. **バージョン番号**: すべてのリリースで統一（例: v1.0.0）
2. **リリースノート**: 各バージョンの特徴と必要環境を明記
3. **ハッシュ値**: 各ファイルのSHA256ハッシュを提供
4. **ライセンス**: LICENSE.txtを各パッケージに含める
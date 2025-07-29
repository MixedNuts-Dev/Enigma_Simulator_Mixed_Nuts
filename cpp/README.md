# Enigma Machine Simulator - C++版

## 概要

第二次世界大戦で使用されたドイツの暗号機「エニグマ」のシミュレーターのC++実装です。高速な暗号化処理とBombe攻撃ツールを含んでいます。

## 機能

- **エニグマ暗号機シミュレーション**
  - 8種類のローター（I-VIII）
  - 2種類のリフレクター（B, C）
  - プラグボード設定
  - リング設定（Ringstellung）
  - マルチスレッド対応
  
- **Bombe攻撃ツール**
  - 既知平文攻撃（クリブアタック）
  - 電気経路追跡による制約伝播アルゴリズム
  - プラグボード配線の自動推定
  - OpenMPによる並列処理
  - 全ローター順序の探索オプション
  - プラグボードなし探索モード
  - 部分一致検出（50%以上のマッチ）
  - 高速な総当たり攻撃

## 必要要件

- C++11以上対応のコンパイラ
- Visual Studio 2022（Windows）
- CMake 3.10以上（オプション）
- OpenMP対応（並列処理用）

## プロジェクト構造

```
cpp/
├── src/
│   ├── core/                # コア暗号化機能
│   │   ├── EnigmaMachine.h  # エニグマクラス定義
│   │   ├── EnigmaMachine.cpp # エニグマ実装
│   │   ├── Rotor.h          # ローターヘッダー
│   │   ├── Rotor.cpp        # ローター実装
│   │   ├── Reflector.h      # リフレクターヘッダー
│   │   ├── Reflector.cpp    # リフレクター実装
│   │   ├── Plugboard.h      # プラグボードヘッダー
│   │   ├── Plugboard.cpp    # プラグボード実装
│   │   ├── RotorConfig.h    # ローター設定
│   │   ├── BombeAttack.h    # Bombe攻撃ヘッダー
│   │   └── BombeAttack.cpp  # Bombe攻撃実装
│   └── main_console.cpp     # メインプログラム
├── build/                   # ビルド出力ディレクトリ
├── CMakeLists.txt           # CMake設定
├── build.bat                # Windowsビルドスクリプト
├── run_enigma.bat           # Windows実行スクリプト
└── README.md                # このファイル
```

## インストール

### 方法1: Visual Studio 2022（Windows）

1. Visual Studio 2022を起動
2. 「フォルダーを開く」でcppディレクトリを選択
3. CMakeプロジェクトとして認識される
4. ビルド構成を選択（Debug/Release）
5. ビルド → すべてビルド

### 方法2: コマンドライン（Windows）

```cmd
# ビルドスクリプトを実行
build.bat

# または手動でビルド
mkdir build
cd build
cmake ..
cmake --build . --config Release
```

### 方法3: Linux/Mac

```bash
# ビルドディレクトリ作成
mkdir build && cd build

# CMakeでプロジェクト生成
cmake ..

# ビルド
make -j4
```

## 実行方法

### Windows

```cmd
# 直接実行
build\Release\EnigmaSimulatorCpp.exe
```

### Linux/Mac

```bash
./build/EnigmaSimulatorCpp
```

## 使用方法

### コマンドラインインターフェース

```bash
# 基本的な暗号化
EnigmaSimulatorCpp -e "HELLO WORLD"

# ローター設定を指定
EnigmaSimulatorCpp -r I,V,III -p A,B,C -e "SECRET MESSAGE"

# 設定ファイルを使用
EnigmaSimulatorCpp -c config.json

# Bombe攻撃モード
EnigmaSimulatorCpp -b --cipher "QMJIDO MZWZJFJR" --crib "HELLO WORLD"

# プラグボードなしでのBombe攻撃
EnigmaSimulatorCpp -b --cipher "QMJIDO MZWZJFJR" --crib "HELLO WORLD" --no-plugboard

# 全ローター順序をテスト
EnigmaSimulatorCpp -b --cipher "QMJIDO MZWZJFJR" --crib "HELLO WORLD" --all-rotors
```

### 対話モード

```bash
EnigmaSimulatorCpp -i
```

対話モードでは以下のコマンドが使用可能：
- `set rotor <position> <type>` - ローター設定
- `set position <rotor> <letter>` - 初期位置設定
- `set ring <rotor> <number>` - リング設定
- `set reflector <type>` - リフレクター設定
- `set plugboard <pairs>` - プラグボード設定
- `encode <message>` - メッセージ暗号化
- `save <filename>` - 設定保存
- `load <filename>` - 設定読み込み
- `bombe` - Bombe攻撃モード
- `help` - ヘルプ表示
- `quit` - 終了

## 設定ファイル

設定はJSON形式で保存・読み込みが可能です：

```json
{
  "rotors": [
    {"type": "I", "position": "A", "ring": 1},
    {"type": "V", "position": "B", "ring": 1},
    {"type": "III", "position": "C", "ring": 1}
  ],
  "reflector": "B",
  "plugboard": "AB CD EF GH IJ KL",
  "message": "HELLO WORLD"
}
```

## ビルドオプション

### CMakeオプション

```bash
# デバッグビルド
cmake -DCMAKE_BUILD_TYPE=Debug ..

# リリースビルド（最適化）
cmake -DCMAKE_BUILD_TYPE=Release ..

# OpenMP無効化
cmake -DUSE_OPENMP=OFF ..

# 静的リンク
cmake -DBUILD_STATIC=ON ..
```

### Visual Studioでの設定

1. プロジェクトプロパティを開く
2. C/C++ → 最適化 → 「速度優先」に設定
3. C/C++ → 言語 → 「OpenMPサポート」を有効化
4. リンカー → 入力 → 追加の依存ファイルに必要なライブラリを追加

## パフォーマンス最適化

- **並列処理**: OpenMPによるマルチスレッド処理
- **ルックアップテーブル**: 高速な文字変換
- **キャッシュ最適化**: メモリアクセスパターンの最適化
- **インライン展開**: 頻繁に呼ばれる関数のインライン化

## トラブルシューティング

### ビルドエラー

1. **C++11サポート不足**
   ```
   cmake -DCMAKE_CXX_STANDARD=11 ..
   ```

2. **OpenMPが見つからない**
   ```
   cmake -DUSE_OPENMP=OFF ..
   ```

3. **文字コードの問題**
   - ソースファイルがUTF-8であることを確認
   - Visual Studioで「詳細保存オプション」からUTF-8を選択

### 実行時エラー

1. **DLLが見つからない**
   - Visual C++再頒布可能パッケージをインストール
   - または静的リンクでビルド

2. **パフォーマンスが遅い**
   - Releaseビルドを使用
   - OpenMPが有効になっているか確認

## 技術詳細

- **Bombeアルゴリズム**:
  - 制約伝播による効率的なプラグボード推定
  - 電気経路追跡シミュレーション
  - 双方向マッピングの競合検出
  - `hasPlugboardConflict_`フラグによる状態管理
- **言語標準**: C++11
- **並列処理**: OpenMP
- **ビルドシステム**: CMake
- **最適化**: -O3（GCC/Clang）、/O2（MSVC）

## ベンチマーク

Intel Core i7-9700K（8コア）での性能：
- 単一メッセージ暗号化: < 1μs
- Bombe攻撃（総当たり）: 約30秒/10^6設定

## ライセンス

MITライセンス

## 作者

[Mixed Nuts tukasa]

## 参考文献

- [Enigma machine - Wikipedia](https://en.wikipedia.org/wiki/Enigma_machine)
- [Bombe - Wikipedia](https://en.wikipedia.org/wiki/Bombe)
- [Modern C++ Design](https://en.cppreference.com/)
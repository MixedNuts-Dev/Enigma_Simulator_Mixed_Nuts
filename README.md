# Enigma Machine Simulator

## 概要

第二次世界大戦で使用されたドイツの暗号機「エニグマ」の歴史的に正確なシミュレーターです。Python、Java、C++の3つの実装を提供し、それぞれがエニグマ暗号機の完全な機能とBombe攻撃ツールを含んでいます。

## 特徴

- 🔐 **完全なエニグマ機能**: 8種類のローター、2種類のリフレクター、プラグボード、リング設定
- 🔓 **高度なBombe攻撃ツール**: 
  - 電気経路追跡による制約伝播アルゴリズム
  - プラグボード配線の自動推定
  - 部分一致検出（50%以上のマッチ）
  - プラグボードなし探索モード
- 🌍 **マルチ言語実装**: Python、Java、C++での統一されたアルゴリズム実装
- 🖥️ **クロスプラットフォーム**: Windows、Linux、macOSで動作
- 📚 **教育目的**: 暗号学の歴史と原理を学ぶための教材として最適

## プロジェクト構造

```
Enigma_demo/
├── python/              # Python実装
│   ├── src/            # モジュール化されたソースコード
│   ├── dist/           # ビルド済み実行ファイル
│   ├── main.py         # メインエントリポイント
│   ├── enigma.py       # 互換性用エントリポイント
│   └── README.md       # Python版詳細ドキュメント
├── java/               # Java実装
│   ├── src/            # Javaソースコード
│   ├── target/         # ビルド出力
│   ├── pom.xml         # Maven設定
│   ├── run_enigma.bat  # Windows実行スクリプト
│   └── README.md       # Java版詳細ドキュメント
├── cpp/                # C++実装
│   ├── src/            # C++ソースコード
│   ├── build/          # ビルド出力
│   ├── CMakeLists.txt  # CMake設定
│   ├── build.bat       # ビルドスクリプト
│   ├── run_enigma.bat  # 実行スクリプト
│   └── README.md       # C++版詳細ドキュメント
└── README.md           # このファイル
```

## クイックスタート

### Python版

```bash
cd python
python main.py
```

### Java版

```bash
cd java
# Mavenでビルド
mvn clean package
java -jar target/enigma-simulator-1.0.jar
# またはバッチファイル（Windows）
run_enigma.bat
```

### C++版

```bash
cd cpp
# ビルド
mkdir build && cd build
cmake .. && make
# 実行（CLI版）
./enigma_console_cpp
# 実行（GUI版 - Qt6が必要）
./enigma_gui_cpp
# またはバッチファイル（Windows）
run_enigma.bat
```

## 機能比較

| 機能 | Python | Java | C++ |
|------|--------|------|-----|
| GUI | ✅ Tkinter | ✅ JavaFX | ✅ Qt6 |
| Bombe攻撃 | ✅ | ✅ | ✅ |
| 並列処理 | ✅ multiprocessing | ✅ ExecutorService | ✅ OpenMP |
| 設定ファイル | ✅ JSON | ✅ JSON | ✅ JSON |
| 実行ファイル | ✅ .exe | ✅ .jar | ✅ .exe |
| クロスプラットフォーム | ✅ | ✅ | ✅ |

## エニグマの仕組み

### 基本構成

1. **ローター（Rotors）**: 文字を別の文字に変換する回転式ディスク
   - 8種類（I-VIII）から3つを選択
   - 各ローターは異なる配線とノッチ位置を持つ

2. **リフレクター（Reflector）**: 信号を反射して折り返す固定ディスク
   - 2種類（B, C）から選択

3. **プラグボード（Plugboard）**: 文字のペアを入れ替える配線盤
   - 最大10ペアまで設定可能

4. **リング設定（Ring Setting）**: ローターの内部配線をずらす設定

### 暗号化プロセス

1. キー入力 → プラグボード → ローター（右→左） → リフレクター
2. リフレクター → ローター（左→右） → プラグボード → 出力
3. キー入力ごとにローターが回転（ダブルステッピング機構）

## Bombe攻撃

Bombe攻撃は、既知の平文（クリブ）を使用してエニグマの設定を解読する高度な手法です：

### アルゴリズムの特徴

1. **電気経路追跡シミュレーション**
   - エニグマの内部配線を通る電気信号をシミュレート
   - プラグボードなしでの文字変換経路を追跡

2. **制約伝播アルゴリズム**
   - プラグボード配線の制約を双方向に伝播
   - 矛盾検出による効率的な探索空間の削減

3. **Diagonal Board実装**
   - 史実のBombeで使用された矛盾検出機構を再現
   - 自己ステッカー（文字が自分自身にマップ）を即座に検出
   - Union-Find構造による効率的な接続コンポーネント管理
   - 3文字以上の循環や奇数サイズのコンポーネントなどの矛盾を高速検出

4. **部分一致対応**
   - 完全一致だけでなく50%以上の部分一致も検出
   - プラグボードが推定できない場合の候補も保持

5. **並列処理による高速化**
   - Python: multiprocessing
   - Java: CompletableFuture
   - C++: OpenMP

## 使用例

### 基本的な暗号化

```python
# Python
from src.core import EnigmaMachine, Rotor, Reflector, Plugboard
enigma = EnigmaMachine(rotors, reflector, plugboard)
encrypted = enigma.encrypt("HELLO WORLD")
```

```java
// Java
EnigmaMachine enigma = new EnigmaMachine(rotors, reflector, plugboard);
String encrypted = enigma.encrypt("HELLO WORLD");
```

```cpp
// C++
EnigmaMachine enigma(rotors, reflector, plugboard);
std::string encrypted = enigma.encrypt("HELLO WORLD");
```

## 教育用途

このシミュレーターは以下の学習に最適です：

- 🔐 **暗号学の歴史**: 第二次世界大戦の暗号技術
- 🧮 **アルゴリズム**: 置換暗号と総当たり攻撃
- 💻 **プログラミング**: マルチ言語実装の比較
- 🔄 **並列処理**: 各言語での並列化手法

## 貢献

プルリクエストを歓迎します！以下の点にご注意ください：

1. 各言語の実装は独立して動作すること
2. 歴史的な正確性を保つこと
3. 適切なドキュメントを含めること

## ライセンス

MITライセンス - 詳細は[LICENSE](LICENSE)ファイルを参照

## 謝辞

- Alan Turingと Bletchley Parkの暗号解読者たち
- エニグマ機の歴史的資料を提供する各種博物館
- オープンソースコミュニティ

## 参考文献

- [Enigma machine - Wikipedia](https://en.wikipedia.org/wiki/Enigma_machine)
- [Bombe - Wikipedia](https://en.wikipedia.org/wiki/Bombe)
- [Bletchley Park](https://bletchleypark.org.uk/)
- [Crypto Museum](https://www.cryptomuseum.com/crypto/enigma/)

## 作者

[Mixed Nuts tukasa]

---

⚠️ **注意**: このソフトウェアは教育目的のみに使用してください。実際の機密情報の暗号化には使用しないでください。
# Enigma Machine Simulator - Java版

## 概要

第二次世界大戦で使用されたドイツの暗号機「エニグマ」のシミュレーターのJava実装です。JavaFXを使用したGUIインターフェースとBombe攻撃ツールを含んでいます。

## 機能

- **エニグマ暗号機シミュレーション**
  - 8種類のローター（I-VIII）
  - 2種類のリフレクター（B, C）
  - プラグボード設定
  - リング設定（Ringstellung）
  
- **Bombe攻撃ツール**
  - 既知平文攻撃（クリブアタック）
  - 電気経路追跡による制約伝播アルゴリズム
  - プラグボード配線の自動推定
  - 並列処理による高速総当たり攻撃
  - 全ローター順序の探索オプション
  - プラグボードなし探索モード
  - 部分一致検出（50%以上のマッチ）
  - プログレスバーでの進捗表示

## 必要要件

- Java 8以上（JavaFX含む）
- Maven（ビルド用）
- Visual Studio 2022（Windows版のバッチファイル実行用）

## プロジェクト構造

```
java/
├── src/
│   └── main/
│       └── java/
│           └── com/
│               └── enigma/
│                   ├── core/                   # コア暗号化機能
│                   │   ├── EnigmaMachine.java  # エニグマ本体
│                   │   ├── Rotor.java          # ローター実装
│                   │   ├── Reflector.java      # リフレクター実装
│                   │   ├── Plugboard.java      # プラグボード実装
│                   │   └── RotorConfig.java    # ローター設定
│                   ├── bombe/                  # Bombe攻撃機能
│                   │   └── BombeAttack.java    # Bombe攻撃実装
│                   └── gui/                    # GUIコンポーネント
│                       ├── EnigmaGUI.java      # メインGUI
│                       └── BombeGUI.java       # Bombe攻撃GUI
├── target/                                     # ビルド出力
├── pom.xml                                     # Maven設定
├── run_enigma.bat                             # Windows実行用バッチ
├── download-javafx-jars.bat                    # JavaFX自動ダウンロードバッチ
└── README.md                                   # このファイル
```

## インストール

### 方法1: Mavenを使用したビルド

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/Enigma_demo.git
cd Enigma_demo/java

# Mavenでビルド
mvn clean package

# 実行
java -jar target/enigma-simulator-1.0.jar
```

### 方法2: バッチファイルを使用（Windows）

```bash
# バッチファイルをダブルクリックまたはコマンドラインから実行
run_enigma.bat
```

## 実行方法

### コマンドラインから

```bash
# JARファイルを直接実行
java -jar target/enigma-simulator-1.0.jar

# 設定ファイルを指定して実行
java -jar target/enigma-simulator-1.0.jar config.json
```

### バッチファイル（Windows）

`run_enigma.bat`をダブルクリックするか、コマンドプロンプトから実行：

```cmd
run_enigma.bat
```

## 使用方法

### エニグマシミュレーター

1. **ローター設定**
   - 3つのローターを選択（I-VIII）
   - 初期位置を設定（A-Z）
   - リング設定を調整（1-26）

2. **リフレクター選択**
   - BまたはCを選択

3. **プラグボード設定**（オプション）
   - 文字ペアを入力（例: "AB CD EF"）
   - 最大10ペアまで設定可能

4. **メッセージの暗号化**
   - メッセージを入力して「Encode」ボタンをクリック
   - 結果が下部に表示されます

### Bombe攻撃ツール

1. メインウィンドウで「Bombe Attack」ボタンをクリック
2. 暗号文を「Cipher Text」フィールドに入力
3. 既知の平文（クリブ）を「Crib」フィールドに入力
4. 「Start Attack」をクリックして攻撃開始
5. 結果から最適な設定を選択
6. 「Export Settings」で設定をメインウィンドウに適用

## 設定ファイル

設定はJSON形式で保存・読み込みが可能です：

```json
{
  "rotors": [
    {"type": "I", "position": "A", "ring": 1},
    {"type": "II", "position": "A", "ring": 1},
    {"type": "III", "position": "A", "ring": 1}
  ],
  "reflector": "B",
  "plugboard": "AB CD EF",
  "message": "HELLO"
}
```

## ビルド方法

### Maven使用

```bash
# クリーンビルド
mvn clean package

# 依存関係を含むJARファイルの作成
mvn clean compile assembly:single
```

### IDE使用

1. IntelliJ IDEAまたはEclipseでプロジェクトを開く
2. Mavenプロジェクトとしてインポート
3. `EnigmaApp.java`を実行

## トラブルシューティング

### JavaFXが見つからない場合

Java 11以降ではJavaFXが別途必要です：

1. **自動ダウンロード（Windows）**:
   ```cmd
   # JavaFXを自動でダウンロードするバッチファイルを実行
   download-javafx-jars.bat
   ```

2. **手動設定**:
   ```bash
   # JavaFXランタイムをダウンロードして実行
   java --module-path /path/to/javafx/lib --add-modules javafx.controls,javafx.fxml -jar enigma-simulator.jar
   ```

### バッチファイルが動作しない場合

1. Java環境変数が設定されているか確認
2. `java -version`でJavaがインストールされているか確認
3. パスにスペースが含まれる場合は引用符で囲む

## 技術詳細

- **Bombeアルゴリズム**:
  - 制約伝播による効率的なプラグボード推定
  - 電気経路追跡シミュレーション
  - 双方向マッピングの競合検出
  - **Diagonal Board実装**: 史実のBombeで使用された高速矛盾検出機構
    - 自己ステッカー（self-stecker）の即座検出
    - Union-Find構造による接続コンポーネント管理
    - 循環や奇数サイズコンポーネントなどの矛盾を効率的に検出
- **GUI**: JavaFX
- **並列処理**: Java Concurrency API (`CompletableFuture`, `ExecutorService`)
- **ビルドツール**: Maven
- **最小Java版**: Java 8

## ライセンス

MITライセンス

## 作者

[Mixed Nuts tukasa]

## 参考文献

- [Enigma machine - Wikipedia](https://en.wikipedia.org/wiki/Enigma_machine)
- [Bombe - Wikipedia](https://en.wikipedia.org/wiki/Bombe)
- [JavaFX Documentation](https://openjfx.io/)
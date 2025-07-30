# Enigma Machine & Bombe Simulator - Java版設計書

## 1. システム概要

### 1.1 目的
Java Swingを使用したエニグマ暗号機とBombeシミュレータの実装。クロスプラットフォーム対応と、オブジェクト指向設計による保守性の高いシステムを提供します。

### 1.2 主要機能
- エニグマ暗号機の完全なシミュレーション
- Bombe攻撃による暗号解読
- Swing GUIによる操作
- 並列処理による高速化（CompletableFuture）
- JSON形式での設定管理

## 2. アーキテクチャ設計

### 2.1 プロジェクト構造
```
java/
├── src/main/java/com/enigma/
│   ├── core/               # コアコンポーネント
│   │   ├── EnigmaMachine.java
│   │   ├── Rotor.java
│   │   ├── Reflector.java
│   │   ├── Plugboard.java
│   │   ├── DiagonalBoard.java
│   │   └── RotorConfig.java
│   ├── bombe/              # Bombe攻撃
│   │   ├── BombeAttack.java
│   │   └── BombeResult.java
│   ├── gui/                # GUI
│   │   ├── EnigmaGUI.java
│   │   └── BombeGUI.java
│   └── utils/              # ユーティリティ
│       └── FileUtils.java
├── pom.xml
└── README.md
```

### 2.2 パッケージ構成
- `com.enigma.core`: エニグマのコア機能
- `com.enigma.bombe`: Bombe攻撃の実装
- `com.enigma.gui`: Swing GUIコンポーネント
- `com.enigma.utils`: 共通ユーティリティ

## 3. コアコンポーネント詳細

### 3.1 Rotorクラス
**パッケージ**: `com.enigma.core`

**責務**:
- ローターの配線と回転機構
- ノッチによる連動
- リング設定の管理

**主要フィールド**:
```java
private final String wiring;
private final int[] notchPositions;
private int position;
private int ringSetting;
private final int[] forwardWiring;
private final int[] backwardWiring;
```

**主要メソッド**:
- `encode(int index, boolean reverse)`: 文字のエンコード
- `rotate()`: ローターの回転
- `isAtNotch()`: ノッチ位置の判定
- `setPosition(int position)`: 位置設定
- `setRing(int ring)`: リング設定

### 3.2 Reflectorクラス
**パッケージ**: `com.enigma.core`

**責務**:
- 反射板による文字の反射
- B型、C型の実装

**主要フィールド**:
```java
private final String wiring;
private final int[] reflectionTable;
```

**主要メソッド**:
- `reflect(int index)`: 文字の反射

### 3.3 Plugboardクラス
**パッケージ**: `com.enigma.core`

**責務**:
- プラグボード接続の管理
- 最大10組の制限
- 双方向マッピング

**定数**:
```java
public static final int MAX_PAIRS = 10;
```

**主要メソッド**:
- `encode(char letter)`: プラグボード変換
- `validateConnections(List<String> connections)`: 接続検証
- `getConnections()`: 現在の接続取得

### 3.4 EnigmaMachineクラス
**パッケージ**: `com.enigma.core`

**責務**:
- エニグマ全体の制御
- コンポーネントの統合
- 暗号化/復号化

**主要フィールド**:
```java
private final List<Rotor> rotors;
private final Reflector reflector;
private final Plugboard plugboard;
```

**主要メソッド**:
- `encrypt(String text)`: テキスト暗号化
- `processChar(char c)`: 単一文字処理
- `reset()`: 初期化
- `setRotorPositions(int[] positions)`: ローター位置設定

### 3.5 DiagonalBoardクラス
**パッケージ**: `com.enigma.core`

**責務**:
- プラグボード仮説の矛盾検出
- Union-Find構造の実装
- 効率的な推移的閉包の計算

**主要メソッド**:
- `testHypothesis(Map<Character, Character> wiring)`: 仮説検証
- `hasSelfStecker(Map<Character, Character> wiring)`: 自己接続検出
- `hasContradiction(Map<Character, Character> wiring)`: 矛盾検出
- `checkTransitiveClosure(Map<Character, Character> wiring)`: 推移的閉包検証

## 4. Bombe攻撃実装

### 4.1 BombeAttackクラス
**パッケージ**: `com.enigma.bombe`

**責務**:
- クリブベース攻撃の実装
- 並列処理による高速化
- 結果の収集と評価

**主要フィールド**:
```java
private final String cribText;
private final String cipherText;
private final List<String> rotorTypes;
private final String reflectorType;
private final boolean testAllOrders;
private final boolean searchWithoutPlugboard;
private volatile boolean stopRequested;
```

**主要メソッド**:
- `run()`: 攻撃の実行
- `testRotorPositions(List<String> rotorOrder)`: ローター位置テスト
- `estimatePlugboard(EnigmaMachine enigma, String crib, String cipher, int offset)`: プラグボード推定
- `calculateScore(String decrypted, String crib)`: スコア計算

**並列処理の実装**:
```java
ExecutorService executor = Executors.newFixedThreadPool(
    Runtime.getRuntime().availableProcessors()
);
List<CompletableFuture<List<BombeResult>>> futures = new ArrayList<>();
```

### 4.2 BombeResultクラス
**パッケージ**: `com.enigma.bombe`

**責務**:
- 攻撃結果の保持
- JSON形式へのシリアライズ

**主要フィールド**:
```java
private final String position;
private final String rotors;
private final double score;
private final double matchRate;
private final List<String> plugboard;
private final int offset;
```

## 5. GUI設計

### 5.1 EnigmaGUIクラス
**パッケージ**: `com.enigma.gui`

**責務**:
- メインウィンドウの実装
- エニグマ設定UI
- ファイルI/O

**主要コンポーネント**:
- ローター設定パネル（JComboBox、JTextField）
- プラグボード入力（JTextField）
- メッセージI/O（JTextArea）
- 操作ボタン（JButton）

**イベントハンドリング**:
```java
encryptButton.addActionListener(e -> encrypt());
saveButton.addActionListener(e -> saveConfiguration());
loadButton.addActionListener(e -> loadConfiguration());
importBombeButton.addActionListener(e -> importBombeResult());
```

### 5.2 BombeGUIクラス
**パッケージ**: `com.enigma.gui`

**責務**:
- Bombe攻撃ウィンドウ
- 攻撃パラメータ設定
- 結果の表示

**主要コンポーネント**:
- クリブ/暗号文入力（JTextArea）
- ローター選択（JCheckBox）
- 進捗表示（JProgressBar）
- 結果リスト（JList）

**スレッド管理**:
```java
SwingWorker<List<BombeResult>, String> worker = 
    new SwingWorker<List<BombeResult>, String>() {
        @Override
        protected List<BombeResult> doInBackground() {
            // Bombe攻撃の実行
        }
    };
```

## 6. ユーティリティ

### 6.1 FileUtilsクラス
**パッケージ**: `com.enigma.utils`

**責務**:
- JSON形式のファイルI/O
- 設定の保存/読み込み

**主要メソッド**:
- `saveConfiguration(File file, Map<String, Object> config)`: 設定保存
- `loadConfiguration(File file)`: 設定読み込み
- `exportBombeResults(File file, List<BombeResult> results)`: 結果エクスポート

### 6.2 RotorConfigクラス
**パッケージ**: `com.enigma.core`

**責務**:
- ローター定義の管理
- 静的定数の提供

**定数定義**:
```java
public static final Map<String, RotorDefinition> ROTOR_DEFINITIONS;
public static final Map<String, ReflectorDefinition> REFLECTOR_DEFINITIONS;
```

## 7. データフォーマット

### 7.1 設定ファイル形式
```json
{
    "rotors": {
        "types": ["I", "II", "III"],
        "positions": ["A", "B", "C"],
        "rings": ["A", "A", "A"]
    },
    "reflector": "B",
    "plugboard": "AB CD EF GH IJ KL MN OP QR ST",
    "message": "HELLO WORLD"
}
```

### 7.2 Bombe結果形式（標準フォーマット）
```json
{
    "timestamp": "2024-01-20T12:00:00",
    "settings": {
        "crib": "WETTERVORHERSAGE",
        "cipher": "SMZNHRXOWFPQJCAI",
        "reflector": "B",
        "testAllOrders": true,
        "searchWithoutPlugboard": false
    },
    "results": [
        {
            "position": "AAA",
            "rotors": "I-II-III",
            "score": 10.5,
            "matchRate": 0.75,
            "plugboard": ["AB", "CD", "EF"],
            "offset": 0
        }
    ]
}
```

## 8. 並列処理とパフォーマンス

### 8.1 CompletableFuture利用
- 非同期処理による応答性向上
- CPUコア数に応じたスレッドプール
- 結果の非同期収集

### 8.2 最適化手法
- 事前計算されたルックアップテーブル
- 配列ベースの高速文字変換
- 効率的な探索空間の削減

### 8.3 メモリ管理
- 大規模な結果セットのストリーミング処理
- 弱参照による不要オブジェクトの解放
- 適切なバッファサイズの設定

## 9. エラーハンドリング

### 9.1 例外設計
```java
public class EnigmaException extends Exception
public class InvalidRotorException extends EnigmaException
public class PlugboardException extends EnigmaException
```

### 9.2 検証ロジック
- 入力文字の範囲チェック（A-Z）
- プラグボード接続数の制限
- ローター設定の妥当性

## 10. テスト戦略

### 10.1 単体テスト（JUnit）
- 各コンポーネントの独立テスト
- 境界値テスト
- 異常系テスト

### 10.2 統合テスト
- エンドツーエンドの暗号化/復号化
- Bombe攻撃の成功率検証
- GUI操作のシナリオテスト

## 11. セキュリティ考慮事項

### 11.1 入力検証
- SQLインジェクション対策（該当しない）
- パストラバーサル対策（ファイルI/O）
- バッファオーバーフロー対策（Java自動管理）

### 11.2 機密情報の扱い
- メモリ上の平文の適切なクリア
- ログ出力時の機密情報マスキング

## 12. 拡張性

### 12.1 プラグインアーキテクチャ
- インターフェースベースの設計
- 新しいローター/リフレクターの追加容易性
- カスタム攻撃アルゴリズムの実装

### 12.2 将来の拡張
- 4ローターエニグマ対応
- より高度な統計的攻撃
- 機械学習ベースの解読支援
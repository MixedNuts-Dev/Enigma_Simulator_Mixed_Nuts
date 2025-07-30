# Enigma Machine & Bombe Simulator - C++版設計書

## 1. システム概要

### 1.1 目的
C++とQtフレームワークを使用した高性能なエニグマ暗号機シミュレータの実装。ネイティブコードによる最高のパフォーマンスと、Qtによるクロスプラットフォーム対応を実現します。

### 1.2 主要機能
- 高速なエニグマ暗号化/復号化エンジン
- マルチスレッドBombe攻撃
- Qt GUIによる直感的な操作
- JSON形式での設定管理
- メモリ効率的な実装

## 2. アーキテクチャ設計

### 2.1 プロジェクト構造
```
cpp/
├── src/
│   ├── core/               # コアエンジン
│   │   ├── EnigmaMachine.h/cpp
│   │   ├── Rotor.h/cpp
│   │   ├── Reflector.h/cpp
│   │   ├── Plugboard.h/cpp
│   │   ├── DiagonalBoard.h/cpp
│   │   └── RotorConfig.h/cpp
│   ├── bombe/              # Bombe攻撃
│   │   ├── BombeAttack.h/cpp
│   │   └── BombeResult.h
│   ├── gui/                # Qt GUI
│   │   ├── EnigmaMainWindow.h/cpp
│   │   └── BombeWindow.h/cpp
│   └── main.cpp
├── CMakeLists.txt
└── README.md
```

### 2.2 名前空間構成
- `enigma`: コア暗号化機能
- `bombe`: Bombe攻撃関連
- `gui`: GUIコンポーネント

## 3. コアコンポーネント詳細

### 3.1 Rotorクラス
**ファイル**: `core/Rotor.h`, `core/Rotor.cpp`

**責務**:
- ローターの配線と回転機構
- ノッチによる連動制御
- リング設定の管理

**主要メンバ**:
```cpp
private:
    std::string wiring_;
    std::vector<int> notchPositions_;
    int position_;
    int ringSetting_;
    std::array<int, 26> forwardWiring_;
    std::array<int, 26> backwardWiring_;
```

**主要メソッド**:
- `int encode(int index, bool reverse) const`: 文字エンコード
- `void rotate()`: ローター回転
- `bool isAtNotch() const`: ノッチ位置判定
- `void setPosition(int position)`: 位置設定
- `void setRing(int ring)`: リング設定

**最適化**:
- `std::array`による固定サイズ配列
- `const`メソッドによる最適化ヒント
- インライン関数の活用

### 3.2 Reflectorクラス
**ファイル**: `core/Reflector.h`, `core/Reflector.cpp`

**責務**:
- 反射板による文字反射
- B型、C型リフレクターの実装

**主要メンバ**:
```cpp
private:
    std::string wiring_;
    std::array<int, 26> reflectionTable_;
```

**主要メソッド**:
- `int reflect(int index) const`: 文字反射
- `void createReflectionTable()`: テーブル生成

### 3.3 Plugboardクラス
**ファイル**: `core/Plugboard.h`, `core/Plugboard.cpp`

**責務**:
- プラグボード接続管理
- 最大10組の制限実装
- 双方向マッピング

**定数**:
```cpp
static constexpr int MAX_PAIRS = 10;
```

**主要メソッド**:
- `char encode(char letter) const`: プラグボード変換
- `void validateConnections()`: 接続検証
- `const std::map<char, char>& getConnections() const`: 接続取得

### 3.4 EnigmaMachineクラス
**ファイル**: `core/EnigmaMachine.h`, `core/EnigmaMachine.cpp`

**責務**:
- エニグマ全体の制御
- コンポーネント統合
- 暗号化/復号化実行

**主要メンバ**:
```cpp
private:
    std::vector<std::unique_ptr<Rotor>> rotors_;
    std::unique_ptr<Reflector> reflector_;
    std::unique_ptr<Plugboard> plugboard_;
```

**主要メソッド**:
- `std::string encrypt(const std::string& text)`: テキスト暗号化
- `char processChar(char c)`: 単一文字処理
- `void reset()`: 初期化
- `void setRotorPositions(const std::vector<int>& positions)`: ローター位置設定

**メモリ管理**:
- `std::unique_ptr`によるRAII
- ムーブセマンティクスの活用

### 3.5 DiagonalBoardクラス
**ファイル**: `core/DiagonalBoard.h`, `core/DiagonalBoard.cpp`

**責務**:
- プラグボード仮説の矛盾検出
- Union-Find構造の実装
- 効率的な推移的閉包計算

**主要メソッド**:
- `bool testHypothesis(const std::map<char, char>& wiring)`: 仮説検証
- `bool hasSelfStecker(const std::map<char, char>& wiring)`: 自己接続検出
- `bool hasContradiction(const std::map<char, char>& wiring)`: 矛盾検出
- `bool checkTransitiveClosure(const std::map<char, char>& wiring)`: 推移的閉包検証

**最適化**:
- パス圧縮付きUnion-Find
- `std::set`による効率的な集合演算

## 4. Bombe攻撃実装

### 4.1 BombeAttackクラス
**ファイル**: `bombe/BombeAttack.h`, `bombe/BombeAttack.cpp`

**責務**:
- クリブベース攻撃の実装
- マルチスレッド並列処理
- 結果の収集と評価

**主要メンバ**:
```cpp
private:
    std::string cribText_;
    std::string cipherText_;
    std::vector<std::string> rotorTypes_;
    std::string reflectorType_;
    bool testAllOrders_;
    bool searchWithoutPlugboard_;
    std::atomic<bool> stopRequested_;
    std::mutex resultMutex_;
```

**主要メソッド**:
- `std::vector<BombeResult> run()`: 攻撃実行
- `void stop()`: 攻撃中断
- `void setProgressCallback(std::function<void(double, const std::string&)> callback)`: 進捗通知

**並列処理**:
```cpp
std::vector<std::future<std::vector<BombeResult>>> futures;
for (size_t i = 0; i < chunks.size(); ++i) {
    futures.push_back(
        std::async(std::launch::async, 
                  &BombeAttack::processChunk, this, chunks[i])
    );
}
```

### 4.2 BombeResultクラス
**ファイル**: `bombe/BombeResult.h`

**責務**:
- 攻撃結果の保持
- 比較演算子の実装

**構造体定義**:
```cpp
struct BombeResult {
    std::string position;
    std::string rotors;
    double score;
    double matchRate;
    std::vector<std::string> plugboard;
    int offset;
    
    bool operator<(const BombeResult& other) const {
        return score > other.score; // 降順ソート
    }
};
```

## 5. GUI設計（Qt）

### 5.1 EnigmaMainWindowクラス
**ファイル**: `gui/EnigmaMainWindow.h`, `gui/EnigmaMainWindow.cpp`

**責務**:
- メインウィンドウの実装
- エニグマ設定UI
- ファイルI/O処理

**継承**:
```cpp
class EnigmaMainWindow : public QMainWindow {
    Q_OBJECT
```

**主要ウィジェット**:
- `QComboBox* rotor1TypeCombo`: ローター選択
- `QLineEdit* rotor1PosEdit`: 位置入力
- `QLineEdit* plugboardEdit`: プラグボード設定
- `QTextEdit* inputTextEdit`: 入力テキスト
- `QTextEdit* outputTextEdit`: 出力テキスト

**シグナル/スロット**:
```cpp
private slots:
    void onEncryptClicked();
    void onSaveConfigClicked();
    void onLoadConfigClicked();
    void onImportBombeResultClicked();
    void onOpenBombeClicked();
```

### 5.2 BombeWindowクラス
**ファイル**: `gui/BombeWindow.h`, `gui/BombeWindow.cpp`

**責務**:
- Bombe攻撃ウィンドウ
- 攻撃パラメータ設定
- 結果表示と管理

**主要機能**:
- 非同期攻撃実行（`QThread`）
- リアルタイム進捗表示
- 結果のソートとフィルタリング

**スレッド管理**:
```cpp
class BombeWorker : public QObject {
    Q_OBJECT
public:
    void process();
signals:
    void progressUpdate(double progress, QString message);
    void finished(QVector<BombeResult> results);
};
```

## 6. RotorConfig定義
**ファイル**: `core/RotorConfig.h`, `core/RotorConfig.cpp`

**責務**:
- ローター/リフレクター定義の管理
- 静的定数の提供

**定義構造**:
```cpp
namespace enigma {
    struct RotorDefinition {
        std::string wiring;
        std::vector<int> notchPositions;
        int getFirstNotch() const { 
            return notchPositions.empty() ? -1 : notchPositions[0]; 
        }
    };
    
    extern const std::map<std::string, RotorDefinition> ROTOR_DEFINITIONS;
    extern const std::map<std::string, ReflectorDefinition> REFLECTOR_DEFINITIONS;
}
```

## 7. メモリ管理とパフォーマンス

### 7.1 RAII原則
- スマートポインタの使用（`std::unique_ptr`, `std::shared_ptr`）
- 自動的なリソース管理
- 例外安全性の確保

### 7.2 最適化技術
- コンパイラ最適化（`-O3`）
- インライン関数の活用
- キャッシュフレンドリーなデータ構造
- SIMD命令の活用可能性

### 7.3 並列処理
- `std::async`による非同期実行
- `std::thread`によるマルチスレッド
- `std::atomic`による同期

## 8. エラーハンドリング

### 8.1 例外階層
```cpp
class EnigmaException : public std::exception {
    std::string message_;
public:
    explicit EnigmaException(const std::string& msg);
    const char* what() const noexcept override;
};

class InvalidRotorException : public EnigmaException { };
class PlugboardException : public EnigmaException { };
```

### 8.2 エラー処理戦略
- RAII原則による安全なリソース管理
- 例外中立性の維持
- エラーコードとの併用

## 9. ビルドシステム（CMake）

### 9.1 CMakeLists.txt構成
```cmake
cmake_minimum_required(VERSION 3.16)
project(EnigmaMachine)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core Widgets)
qt6_standard_project_setup()

# ソースファイルの追加
add_executable(EnigmaMachine
    src/main.cpp
    src/core/EnigmaMachine.cpp
    # ... 他のソースファイル
)

target_link_libraries(EnigmaMachine Qt6::Core Qt6::Widgets)
```

### 9.2 プラットフォーム対応
- Windows: MSVC 2019+
- macOS: Clang 12+
- Linux: GCC 9+

## 10. テスト戦略

### 10.1 単体テスト
- Google Test フレームワーク
- 各コンポーネントの独立テスト
- エッジケースのカバレッジ

### 10.2 パフォーマンステスト
- ベンチマーク測定
- メモリリーク検出（Valgrind）
- プロファイリング

## 11. セキュリティ考慮事項

### 11.1 バッファオーバーフロー対策
- `std::string`の使用
- 境界チェック
- 安全な文字列操作

### 11.2 整数オーバーフロー対策
- 範囲チェック
- 安全な型変換

## 12. 将来の拡張

### 12.1 GPU活用
- CUDA/OpenCLによる並列化
- 大規模探索の高速化

### 12.2 機能拡張
- 4ローターエニグマ対応
- より高度な暗号解析
- プラグイン機構

### 12.3 最適化
- プロファイルガイド最適化
- アーキテクチャ固有の最適化
- キャッシュ最適化
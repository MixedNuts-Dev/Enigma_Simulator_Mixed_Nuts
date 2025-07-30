# Enigma Machine & Bombe Simulator - Java版クラス図

## 1. コアコンポーネント（com.enigma.core）

```mermaid
classDiagram
    class EnigmaMachine {
        -List~Rotor~ rotors
        -Reflector reflector
        -Plugboard plugboard
        +EnigmaMachine(List~Rotor~ rotors, Reflector reflector, Plugboard plugboard)
        +String encrypt(String text)
        +String decrypt(String text)
        +char processChar(char c)
        +void reset()
        +void setRotorPositions(int[] positions)
        +int[] getRotorPositions()
        -void rotateRotors()
        -char encodeChar(char c)
    }

    class Rotor {
        -String wiring
        -int[] notchPositions
        -int position
        -int ringSetting
        -int[] forwardWiring
        -int[] backwardWiring
        +Rotor(String wiring, int[] notchPositions)
        +int encode(int index, boolean reverse)
        +void rotate()
        +boolean isAtNotch()
        +void setPosition(int position)
        +int getPosition()
        +void setRing(int ring)
        -void createWiringTables()
    }

    class Reflector {
        -String wiring
        -int[] reflectionTable
        +Reflector(String wiring)
        +int reflect(int index)
        -void createReflectionTable()
    }

    class Plugboard {
        +int MAX_PAIRS = 10
        -Map~Character, Character~ connections
        +Plugboard()
        +Plugboard(List~String~ connections)
        +char encode(char letter)
        +Map~Character, Character~ getConnections()
        -void validateConnections(List~String~ connections)
    }

    class DiagonalBoard {
        -List~Set~Character~~ connections
        +DiagonalBoard()
        +boolean testHypothesis(Map~Character, Character~ wiring)
        +boolean hasSelfStecker(Map~Character, Character~ wiring)
        +boolean hasContradiction(Map~Character, Character~ wiring)
        -boolean checkTransitiveClosure(Map~Character, Character~ wiring)
        -int find(int[] parent, int x)
        -void unite(int[] parent, int x, int y)
    }

    class RotorConfig {
        <<static>>
        +Map~String, RotorDefinition~ ROTOR_DEFINITIONS$
        +Map~String, ReflectorDefinition~ REFLECTOR_DEFINITIONS$
        +void initializeDefinitions()$
    }

    class RotorDefinition {
        +String wiring
        +int[] notchPositions
        +RotorDefinition(String wiring, int[] notchPositions)
    }

    class ReflectorDefinition {
        +String wiring
        +ReflectorDefinition(String wiring)
    }

    EnigmaMachine "1" *-- "3" Rotor
    EnigmaMachine "1" *-- "1" Reflector
    EnigmaMachine "1" *-- "1" Plugboard
    RotorConfig ..> RotorDefinition : creates
    RotorConfig ..> ReflectorDefinition : creates
```

## 2. Bombe攻撃コンポーネント（com.enigma.bombe）

```mermaid
classDiagram
    class BombeAttack {
        -String cribText
        -String cipherText
        -List~String~ rotorTypes
        -String reflectorType
        -boolean testAllOrders
        -boolean searchWithoutPlugboard
        -boolean stopRequested
        -Consumer~Double~ progressCallback
        -Consumer~String~ logCallback
        +BombeAttack(String cribText, String cipherText, List~String~ rotorTypes, String reflectorType)
        +void setTestAllOrders(boolean value)
        +void setSearchWithoutPlugboard(boolean value)
        +void setProgressCallback(Consumer~Double~ callback)
        +void setLogCallback(Consumer~String~ callback)
        +List~BombeResult~ run()
        +void stop()
        -List~BombeResult~ testRotorPositions(List~String~ rotorOrder)
        -BombeResult testPosition(int[] positions, List~String~ rotorOrder, int offset)
        -Map.Entry~List~String~, Double~ estimatePlugboard(EnigmaMachine enigma, String crib, String cipher, int offset)
        -double calculateScore(String decrypted, String crib)
        -boolean checkContradiction(DiagonalBoard board, Map~Character, Character~ wiring)
    }

    class BombeResult {
        -String position
        -String rotors
        -double score
        -double matchRate
        -List~String~ plugboard
        -int offset
        +BombeResult(String position, String rotors, double score, double matchRate, List~String~ plugboard, int offset)
        +String getPosition()
        +String getRotors()
        +double getScore()
        +double getMatchRate()
        +List~String~ getPlugboard()
        +int getOffset()
        +int compareTo(BombeResult other)
    }

    class PositionTestTask {
        <<Callable>>
        -int[] positions
        -List~String~ rotorOrder
        -int offset
        -BombeAttack parent
        +PositionTestTask(int[] positions, List~String~ rotorOrder, int offset, BombeAttack parent)
        +BombeResult call()
    }

    BombeAttack ..> BombeResult : creates
    BombeAttack ..> PositionTestTask : creates
    BombeAttack ..> EnigmaMachine : uses
    BombeAttack ..> DiagonalBoard : uses
    PositionTestTask ..> BombeResult : returns
```

## 3. GUI コンポーネント（com.enigma.gui）

```mermaid
classDiagram
    class EnigmaGUI {
        -JFrame frame
        -EnigmaMachine enigmaMachine
        -JComboBox~String~[] rotorCombos
        -JTextField[] positionFields
        -JTextField[] ringFields
        -JComboBox~String~ reflectorCombo
        -JTextField plugboardField
        -JTextArea inputArea
        -JTextArea outputArea
        -JButton encryptButton
        -JButton saveButton
        -JButton loadButton
        -JButton importBombeButton
        -JButton openBombeButton
        +EnigmaGUI()
        +void show()
        -void initializeComponents()
        -void layoutComponents()
        -void setupEventHandlers()
        -void encrypt()
        -void saveConfiguration()
        -void loadConfiguration()
        -void importBombeResult()
        -void openBombeWindow()
        -void updateEnigmaFromUI()
        -String validateInput(String text)
    }

    class BombeGUI {
        -JDialog dialog
        -JTextArea cribArea
        -JTextArea cipherArea
        -JCheckBox[] rotorCheckboxes
        -JComboBox~String~ reflectorCombo
        -JCheckBox testAllOrdersCheck
        -JCheckBox noPlugboardCheck
        -JProgressBar progressBar
        -JList~BombeResult~ resultList
        -DefaultListModel~BombeResult~ listModel
        -JButton startButton
        -JButton stopButton
        -JButton exportButton
        -BombeAttack currentAttack
        -SwingWorker~List~BombeResult~, String~ worker
        +BombeGUI(JFrame parent)
        +void show()
        -void initializeComponents()
        -void layoutComponents()
        -void setupEventHandlers()
        -void startAttack()
        -void stopAttack()
        -void exportResults()
        -void applyResult()
        -void updateProgress(double progress, String message)
    }

    class ResultListCellRenderer {
        <<ListCellRenderer>>
        +Component getListCellRendererComponent(JList list, Object value, int index, boolean isSelected, boolean cellHasFocus)
    }

    EnigmaGUI ..> EnigmaMachine : uses
    EnigmaGUI ..> BombeGUI : creates
    BombeGUI ..> BombeAttack : creates
    BombeGUI ..> BombeResult : displays
    BombeGUI ..> ResultListCellRenderer : uses
```

## 4. ユーティリティ（com.enigma.utils）

```mermaid
classDiagram
    class FileUtils {
        <<static>>
        +void saveConfiguration(File file, Map~String, Object~ config)$
        +Map~String, Object~ loadConfiguration(File file)$
        +void exportBombeResults(File file, List~BombeResult~ results, Map~String, Object~ settings)$
        +List~BombeResult~ importBombeResults(File file)$
        -JSONObject mapToJson(Map~String, Object~ map)$
        -Map~String, Object~ jsonToMap(JSONObject json)$
    }

    class ValidationUtils {
        <<static>>
        +String validateEnigmaText(String text)$
        +boolean isValidRotorPosition(String position)$
        +boolean isValidPlugboardPair(String pair)$
        +List~String~ parsePlugboardPairs(String input)$
    }
```

## 5. 並列処理構造

```mermaid
classDiagram
    class ParallelBombeExecutor {
        -ExecutorService executor
        -int threadCount
        +ParallelBombeExecutor()
        +ParallelBombeExecutor(int threadCount)
        +List~Future~List~BombeResult~~~ submitTasks(List~Callable~BombeResult~~ tasks)
        +List~BombeResult~ collectResults(List~Future~List~BombeResult~~~ futures)
        +void shutdown()
    }

    class CompletableFutureChain {
        <<interface>>
        +CompletableFuture~T~ execute()
        +CompletableFuture~T~ handleError(Throwable ex)
    }
```

## 6. 定数とEnum

```mermaid
classDiagram
    class RotorType {
        <<enumeration>>
        I
        II
        III
        IV
        V
        VI
        VII
        VIII
        +String getWiring()
        +int[] getNotchPositions()
    }

    class ReflectorType {
        <<enumeration>>
        B
        C
        +String getWiring()
    }

    class Constants {
        <<static>>
        +int ALPHABET_SIZE = 26$
        +char FIRST_LETTER = 'A'$
        +int MAX_PLUGBOARD_PAIRS = 10$
        +String DEFAULT_REFLECTOR = "B"$
        +String[] DEFAULT_ROTORS = ["I", "II", "III"]$
    }
```

## 7. イベントフロー

### 7.1 暗号化処理フロー
```mermaid
sequenceDiagram
    participant User
    participant EnigmaGUI
    participant EnigmaMachine
    participant Rotor
    participant Reflector
    participant Plugboard

    User->>EnigmaGUI: Click Encrypt
    EnigmaGUI->>EnigmaGUI: updateEnigmaFromUI()
    EnigmaGUI->>EnigmaMachine: encrypt(text)
    loop for each character
        EnigmaMachine->>Plugboard: encode(char)
        EnigmaMachine->>Rotor: encode(index, false) x3
        EnigmaMachine->>Reflector: reflect(index)
        EnigmaMachine->>Rotor: encode(index, true) x3
        EnigmaMachine->>Plugboard: encode(char)
        EnigmaMachine->>EnigmaMachine: rotateRotors()
    end
    EnigmaMachine-->>EnigmaGUI: encrypted text
    EnigmaGUI-->>User: Display result
```

### 7.2 Bombe攻撃フロー
```mermaid
sequenceDiagram
    participant User
    participant BombeGUI
    participant SwingWorker
    participant BombeAttack
    participant ExecutorService
    participant DiagonalBoard

    User->>BombeGUI: Click Start
    BombeGUI->>SwingWorker: execute()
    SwingWorker->>BombeAttack: run()
    BombeAttack->>ExecutorService: submit tasks
    loop for each position
        ExecutorService->>BombeAttack: testPosition()
        BombeAttack->>DiagonalBoard: testHypothesis()
        DiagonalBoard-->>BombeAttack: contradiction result
    end
    ExecutorService-->>BombeAttack: results
    BombeAttack-->>SwingWorker: sorted results
    SwingWorker->>BombeGUI: publish progress
    SwingWorker-->>BombeGUI: done(results)
    BombeGUI-->>User: Display results
```

## 8. 主要な設計パターン

### 8.1 使用パターン
1. **Builder Pattern**: EnigmaMachine構築
2. **Strategy Pattern**: 異なる攻撃アルゴリズム
3. **Observer Pattern**: 進捗通知
4. **Singleton Pattern**: RotorConfig
5. **Factory Pattern**: Rotor/Reflector生成

### 8.2 SOLID原則の適用
- **単一責任**: 各クラスが明確な責務を持つ
- **開放閉鎖**: 新しいローター/リフレクターの追加が容易
- **リスコフ置換**: インターフェースベースの設計
- **インターフェース分離**: 必要最小限のインターフェース
- **依存性逆転**: 抽象に依存し、具象に依存しない

## 9. エラーハンドリング階層

```mermaid
classDiagram
    class Exception {
        <<Java Built-in>>
    }
    
    class EnigmaException {
        +EnigmaException(String message)
        +EnigmaException(String message, Throwable cause)
    }
    
    class InvalidRotorException {
        +InvalidRotorException(String rotorType)
    }
    
    class PlugboardException {
        +PlugboardException(String message)
    }
    
    class BombeException {
        +BombeException(String message)
    }
    
    Exception <|-- EnigmaException
    EnigmaException <|-- InvalidRotorException
    EnigmaException <|-- PlugboardException
    EnigmaException <|-- BombeException
```

## 10. パフォーマンス最適化ポイント

1. **事前計算**: ローター配線テーブルの事前生成
2. **並列処理**: CompletableFutureによる非同期実行
3. **メモリ効率**: プリミティブ配列の使用
4. **キャッシング**: 頻繁に使用される計算結果のキャッシュ
5. **遅延評価**: 必要になるまで計算を遅延
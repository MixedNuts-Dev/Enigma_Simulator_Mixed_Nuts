# Enigma Machine & Bombe Simulator - C++版クラス図

## 1. コアコンポーネント（core/）

```mermaid
classDiagram
    class EnigmaMachine {
        -vector~unique_ptr~Rotor~~ rotors_
        -unique_ptr~Reflector~ reflector_
        -unique_ptr~Plugboard~ plugboard_
        +EnigmaMachine(vector~unique_ptr~Rotor~~, unique_ptr~Reflector~, unique_ptr~Plugboard~)
        +string encrypt(const string& text)
        +string decrypt(const string& text)
        +char processChar(char c)
        +void reset()
        +void setRotorPositions(const vector~int~& positions)
        +vector~int~ getRotorPositions() const
        -void rotateRotors()
        -char encodeChar(char c)
    }

    class Rotor {
        -string wiring_
        -vector~int~ notchPositions_
        -int position_
        -int ringSetting_
        -array~int,26~ forwardWiring_
        -array~int,26~ backwardWiring_
        +Rotor(const string& wiring, const vector~int~& notchPositions)
        +int encode(int index, bool reverse) const
        +void rotate()
        +bool isAtNotch() const
        +void setPosition(int position)
        +int getPosition() const
        +void setRing(int ring)
        -void createWiringTables()
    }

    class Reflector {
        -string wiring_
        -array~int,26~ reflectionTable_
        +Reflector(const string& wiring)
        +int reflect(int index) const
        -void createReflectionTable()
    }

    class Plugboard {
        +static constexpr int MAX_PAIRS = 10
        -map~char,char~ connections_
        +Plugboard()
        +Plugboard(const vector~string~& connections)
        +char encode(char letter) const
        +const map~char,char~& getConnections() const
        -void validateConnections(const vector~string~& connections)
    }

    class DiagonalBoard {
        -vector~set~char~~ connections_
        +DiagonalBoard()
        +bool testHypothesis(const map~char,char~& wiring)
        +bool hasSelfStecker(const map~char,char~& wiring)
        +bool hasContradiction(const map~char,char~& wiring)
        -bool checkTransitiveClosure(const map~char,char~& wiring)
    }

    EnigmaMachine "1" *-- "3" Rotor : unique_ptr
    EnigmaMachine "1" *-- "1" Reflector : unique_ptr
    EnigmaMachine "1" *-- "1" Plugboard : unique_ptr
```

## 2. Bombe攻撃コンポーネント（bombe/）

```mermaid
classDiagram
    class BombeAttack {
        -string cribText_
        -string cipherText_
        -vector~string~ rotorTypes_
        -string reflectorType_
        -bool testAllOrders_
        -bool searchWithoutPlugboard_
        -atomic~bool~ stopRequested_
        -mutex resultMutex_
        -function~void(double,string)~ progressCallback_
        -function~void(string)~ logCallback_
        +BombeAttack(string crib, string cipher, vector~string~ rotors, string reflector)
        +vector~BombeResult~ run()
        +void stop()
        +void setTestAllOrders(bool value)
        +void setSearchWithoutPlugboard(bool value)
        +void setProgressCallback(function~void(double,string)~ callback)
        +void setLogCallback(function~void(string)~ callback)
        -vector~BombeResult~ testRotorPositions(const vector~string~& rotorOrder)
        -BombeResult testPosition(const array~int,3~& positions, const vector~string~& rotorOrder, int offset)
        -pair~vector~string~,double~ estimatePlugboard(EnigmaMachine& enigma, string crib, string cipher, int offset)
        -double calculateScore(const string& decrypted, const string& crib)
        -vector~BombeResult~ processChunk(const vector~array~int,3~~& chunk)
    }

    class BombeResult {
        <<struct>>
        +string position
        +string rotors
        +double score
        +double matchRate
        +vector~string~ plugboard
        +int offset
        +bool operator<(const BombeResult& other) const
    }

    BombeAttack ..> BombeResult : creates
    BombeAttack ..> EnigmaMachine : uses
    BombeAttack ..> DiagonalBoard : uses
```

## 3. GUI コンポーネント（gui/）- Qt

```mermaid
classDiagram
    class QMainWindow {
        <<Qt Framework>>
    }
    
    class QWidget {
        <<Qt Framework>>
    }

    class EnigmaMainWindow {
        -unique_ptr~EnigmaMachine~ enigmaMachine
        -QComboBox* rotor1TypeCombo
        -QComboBox* rotor2TypeCombo
        -QComboBox* rotor3TypeCombo
        -QLineEdit* rotor1PosEdit
        -QLineEdit* rotor2PosEdit
        -QLineEdit* rotor3PosEdit
        -QLineEdit* rotor1RingEdit
        -QLineEdit* rotor2RingEdit
        -QLineEdit* rotor3RingEdit
        -QComboBox* reflectorCombo
        -QLineEdit* plugboardEdit
        -QTextEdit* inputTextEdit
        -QTextEdit* outputTextEdit
        -QPushButton* encryptButton
        -QPushButton* saveConfigButton
        -QPushButton* loadConfigButton
        -QPushButton* importBombeButton
        -QPushButton* openBombeButton
        +EnigmaMainWindow(QWidget* parent = nullptr)
        +~EnigmaMainWindow()
        -void setupUi()
        -void setupEnigmaMachine()
        -void updateEnigmaFromUi()
        -void updateRotorPositions()
        -slots: void onEncryptClicked()
        -slots: void onSaveConfigClicked()
        -slots: void onLoadConfigClicked()
        -slots: void onImportBombeResultClicked()
        -slots: void onOpenBombeClicked()
    }

    class BombeWindow {
        -unique_ptr~BombeAttack~ bombeAttack
        -QThread* workerThread
        -BombeWorker* worker
        -QTextEdit* cribTextEdit
        -QTextEdit* cipherTextEdit
        -QCheckBox* rotorCheckboxes[8]
        -QComboBox* reflectorCombo
        -QCheckBox* testAllOrdersCheck
        -QCheckBox* noPlugboardCheck
        -QProgressBar* progressBar
        -QListWidget* resultsList
        -QPushButton* startButton
        -QPushButton* stopButton
        -QPushButton* exportButton
        -QPushButton* loadSettingsButton
        -QPushButton* saveSettingsButton
        -vector~BombeResult~ currentResults
        +BombeWindow(QWidget* parent = nullptr)
        +~BombeWindow()
        -void setupUi()
        -void connectSignals()
        -slots: void onStartClicked()
        -slots: void onStopClicked()
        -slots: void onExportClicked()
        -slots: void onResultSelected()
        -slots: void onProgressUpdate(double progress, QString message)
        -slots: void onAttackFinished(QVector~BombeResult~ results)
    }

    class BombeWorker {
        -BombeAttack* attack
        +BombeWorker(BombeAttack* attack)
        +slots: void process()
        +signals: void progressUpdate(double progress, QString message)
        +signals: void finished(QVector~BombeResult~ results)
        +signals: void error(QString err)
    }

    QMainWindow <|-- EnigmaMainWindow
    QWidget <|-- BombeWindow
    QObject <|-- BombeWorker
    EnigmaMainWindow ..> BombeWindow : creates
    BombeWindow ..> BombeWorker : creates
    BombeWorker ..> BombeAttack : uses
```

## 4. 設定管理（core/）

```mermaid
classDiagram
    class RotorConfig {
        <<namespace enigma>>
        +static map~string,RotorDefinition~ ROTOR_DEFINITIONS$
        +static map~string,ReflectorDefinition~ REFLECTOR_DEFINITIONS$
    }

    class RotorDefinition {
        <<struct>>
        +string wiring
        +vector~int~ notchPositions
        +int getFirstNotch() const
    }

    class ReflectorDefinition {
        <<struct>>
        +string wiring
    }

    RotorConfig ..> RotorDefinition : contains
    RotorConfig ..> ReflectorDefinition : contains
```

## 5. メモリ管理とスマートポインタ

```mermaid
classDiagram
    class unique_ptr~T~ {
        <<std>>
        +T* get()
        +T* release()
        +void reset(T* ptr)
        +T& operator*()
        +T* operator->()
    }

    class shared_ptr~T~ {
        <<std>>
        +T* get()
        +long use_count()
        +T& operator*()
        +T* operator->()
    }

    class weak_ptr~T~ {
        <<std>>
        +shared_ptr~T~ lock()
        +bool expired()
    }
```

## 6. 並列処理構造

```mermaid
classDiagram
    class thread {
        <<std>>
        +thread(Function&& f, Args&&... args)
        +void join()
        +void detach()
        +bool joinable()
    }

    class future~T~ {
        <<std>>
        +T get()
        +void wait()
        +bool valid()
    }

    class promise~T~ {
        <<std>>
        +void set_value(T value)
        +void set_exception(exception_ptr p)
        +future~T~ get_future()
    }

    class atomic~T~ {
        <<std>>
        +T load()
        +void store(T value)
        +T exchange(T value)
        +bool compare_exchange_strong(T& expected, T desired)
    }

    class mutex {
        <<std>>
        +void lock()
        +void unlock()
        +bool try_lock()
    }

    class lock_guard~Mutex~ {
        <<std>>
        +lock_guard(Mutex& m)
        +~lock_guard()
    }

    BombeAttack ..> thread : uses
    BombeAttack ..> future : uses
    BombeAttack ..> atomic : uses
    BombeAttack ..> mutex : uses
```

## 7. エラー処理階層

```mermaid
classDiagram
    class exception {
        <<std>>
        +const char* what() const
    }

    class runtime_error {
        <<std>>
    }

    class EnigmaException {
        -string message_
        +EnigmaException(const string& msg)
        +const char* what() const noexcept override
    }

    class InvalidRotorException {
        +InvalidRotorException(const string& rotorType)
    }

    class PlugboardException {
        +PlugboardException(const string& message)
    }

    class BombeException {
        +BombeException(const string& message)
    }

    exception <|-- runtime_error
    runtime_error <|-- EnigmaException
    EnigmaException <|-- InvalidRotorException
    EnigmaException <|-- PlugboardException
    EnigmaException <|-- BombeException
```

## 8. Qt シグナル/スロット接続

```mermaid
sequenceDiagram
    participant User
    participant EnigmaMainWindow
    participant BombeWindow
    participant BombeWorker
    participant BombeAttack

    User->>EnigmaMainWindow: Click "Open Bombe"
    EnigmaMainWindow->>BombeWindow: new BombeWindow()
    User->>BombeWindow: Click "Start"
    BombeWindow->>BombeWorker: Create worker
    BombeWindow->>BombeWorker: moveToThread()
    BombeWorker->>BombeAttack: run()
    
    loop Progress Updates
        BombeAttack->>BombeWorker: progressCallback
        BombeWorker-->>BombeWindow: emit progressUpdate()
        BombeWindow-->>User: Update UI
    end
    
    BombeAttack-->>BombeWorker: Results
    BombeWorker-->>BombeWindow: emit finished()
    BombeWindow-->>User: Display results
```

## 9. ファイルI/O構造

```mermaid
classDiagram
    class QJsonDocument {
        <<Qt>>
        +static QJsonDocument fromJson(const QByteArray& json)
        +QByteArray toJson() const
        +QJsonObject object() const
        +void setObject(const QJsonObject& object)
    }

    class QJsonObject {
        <<Qt>>
        +void insert(const QString& key, const QJsonValue& value)
        +QJsonValue value(const QString& key) const
        +bool contains(const QString& key) const
    }

    class QJsonArray {
        <<Qt>>
        +void append(const QJsonValue& value)
        +int size() const
        +QJsonValue at(int i) const
    }

    class FileHandler {
        <<utility>>
        +static bool saveConfiguration(const QString& filename, const QJsonObject& config)
        +static QJsonObject loadConfiguration(const QString& filename)
        +static bool exportBombeResults(const QString& filename, const vector~BombeResult~& results)
        +static vector~BombeResult~ importBombeResults(const QString& filename)
    }

    FileHandler ..> QJsonDocument : uses
    FileHandler ..> QJsonObject : uses
    FileHandler ..> QJsonArray : uses
```

## 10. 定数定義

```mermaid
classDiagram
    class Constants {
        <<namespace>>
        +static constexpr int ALPHABET_SIZE = 26
        +static constexpr char FIRST_LETTER = 'A'
        +static constexpr int MAX_PLUGBOARD_PAIRS = 10
        +static const char* DEFAULT_REFLECTOR = "B"
        +static const char* DEFAULT_ROTORS[] = {"I", "II", "III"}
    }

    class WiringDefinitions {
        <<namespace>>
        +static const char* ROTOR_I = "EKMFLGDQVZNTOWYHXUSPAIBRCJ"
        +static const char* ROTOR_II = "AJDKSIRUXBLHWTMCQGZNPYFVOE"
        +static const char* ROTOR_III = "BDFHJLCPRTXVZNYEIWGAKMUSQO"
        +static const char* ROTOR_IV = "ESOVPZJAYQUIRHXLNFTGKDCMWB"
        +static const char* ROTOR_V = "VZBRGITYUPSDNHLXAWMJQOFECK"
        +static const char* ROTOR_VI = "JPGVOUMFYQBENHZRDKASXLICTW"
        +static const char* ROTOR_VII = "NZJHGRCXMYSWBOUFAIVLPEKQDT"
        +static const char* ROTOR_VIII = "FKQHTLXOCBJSPDZRAMEWNIUYGV"
        +static const char* REFLECTOR_B = "YRUHQSLDPXNGOKMIEBFZCWVJAT"
        +static const char* REFLECTOR_C = "FVPJIAOYEDRZXWGCTKUQSBNMHL"
    }
```

## 11. パフォーマンス最適化ポイント

1. **インライン関数**: 頻繁に呼ばれる小さな関数
2. **const正確性**: コンパイラ最適化のヒント
3. **ムーブセマンティクス**: 不要なコピーの削減
4. **配列ベース**: `std::array`による固定サイズ最適化
5. **並列処理**: `std::async`による非同期実行
6. **キャッシュ最適化**: データ局所性の向上
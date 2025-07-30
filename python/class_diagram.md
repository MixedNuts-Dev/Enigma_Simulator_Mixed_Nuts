# Enigma Machine & Bombe Simulator - Python版クラス図

## 1. コアコンポーネント（core/）

```mermaid
classDiagram
    class EnigmaMachine {
        -rotors: List[Rotor]
        -reflector: Reflector
        -plugboard: Plugboard
        +__init__(rotors, reflector, plugboard)
        +encrypt(text: str) str
        +decrypt(text: str) str
        +process_char(char: str) str
        +reset()
        +set_rotor_positions(positions: List[int])
        +get_rotor_positions() List[int]
        -rotate_rotors()
    }

    class Rotor {
        -wiring: str
        -notch_positions: List[int]
        -position: int
        -ring_setting: int
        -forward_wiring: Dict[int, int]
        -backward_wiring: Dict[int, int]
        +__init__(wiring: str, notch_positions: List[int])
        +encode(index: int, reverse: bool) int
        +rotate()
        +is_at_notch() bool
        +set_position(position: int)
        +get_position() int
        +set_ring(ring: int)
        -create_wiring_tables()
    }

    class Reflector {
        -wiring: str
        -wiring_dict: Dict[int, int]
        +__init__(wiring: str)
        +reflect(index: int) int
        -create_wiring_dict()
    }

    class Plugboard {
        +MAX_PAIRS: int = 10
        -connections: Dict[str, str]
        +__init__(connections: List[str])
        +encode(char: str) str
        -validate_connections(connections: List[str])
    }

    class DiagonalBoard {
        -connections: List[Set[str]]
        +__init__()
        +test_hypothesis(wiring: Dict[str, str]) bool
        +has_self_stecker(wiring: Dict[str, str]) bool
        +has_contradiction(wiring: Dict[str, str]) bool
        -_check_transitive_closure(wiring: Dict[str, str]) bool
    }

    EnigmaMachine "1" *-- "3" Rotor
    EnigmaMachine "1" *-- "1" Reflector
    EnigmaMachine "1" *-- "1" Plugboard
```

## 2. Bombe攻撃コンポーネント（bombe/）

```mermaid
classDiagram
    class BombeAttack {
        -crib_text: str
        -cipher_text: str
        -rotor_types: List[str]
        -reflector_type: str
        -test_all_orders: bool
        -search_without_plugboard: bool
        -log_queue: Queue
        -stop_event: Event
        +__init__(crib_text, cipher_text, rotor_types, reflector_type, log_queue, test_all_orders, search_without_plugboard)
        +run() List[Dict]
        -_test_rotor_positions(rotor_order: List[str]) List[Tuple]
        -_estimate_plugboard(enigma: EnigmaMachine, crib_text: str, cipher_text: str, offset: int) Tuple[List[str], float]
        -_check_contradiction(diagonal_board: DiagonalBoard, wiring: Dict[str, str]) bool
        -_worker_test_positions(positions_batch: List) List[Tuple]
    }

    class OptimizedBombe {
        -rotor_wirings: np.ndarray
        -reflector_wiring: np.ndarray
        -notch_positions: List[np.ndarray]
        +__init__(rotor_types: List[str], reflector_type: str)
        +encrypt_batch(texts: np.ndarray, positions: np.ndarray) np.ndarray
        -_setup_wirings(rotor_types: List[str], reflector_type: str)
    }

    BombeAttack ..> OptimizedBombe : uses
    BombeAttack ..> DiagonalBoard : uses
    BombeAttack ..> EnigmaMachine : creates
```

## 3. GUI コンポーネント

```mermaid
classDiagram
    class EnigmaGUI {
        -root: tk.Tk
        -enigma_machine: EnigmaMachine
        -rotor_vars: Dict[str, tk.StringVar]
        -reflector_var: tk.StringVar
        -plugboard_var: tk.StringVar
        -input_text: tk.Text
        -output_text: tk.Text
        +__init__()
        -setup_ui()
        -create_rotor_frame() tk.Frame
        -create_io_frame() tk.Frame
        -create_button_frame() tk.Frame
        -encrypt_decrypt()
        -save_config()
        -load_config()
        -import_bombe_result()
        -open_bombe_window()
        -update_enigma_from_ui()
        -validate_input(text: str) str
    }

    class BombeGUI {
        -root: tk.Toplevel
        -crib_text: tk.Text
        -cipher_text: tk.Text
        -rotor_checkboxes: Dict[str, tk.BooleanVar]
        -reflector_var: tk.StringVar
        -test_all_var: tk.BooleanVar
        -no_plugboard_var: tk.BooleanVar
        -progress_var: tk.DoubleVar
        -result_listbox: tk.Listbox
        -results: List[Dict]
        -attack_thread: Thread
        -stop_event: Event
        +__init__(parent: tk.Tk)
        -setup_ui()
        -start_attack()
        -stop_attack()
        -update_progress(value: float, message: str)
        -display_results(results: List[Dict])
        -export_results()
        -load_settings()
        -save_settings()
        -apply_result_to_enigma()
    }

    EnigmaGUI ..> EnigmaMachine : uses
    BombeGUI ..> BombeAttack : creates
    EnigmaGUI ..> BombeGUI : opens
```

## 4. ユーティリティとヘルパー

```mermaid
classDiagram
    class process_positions_batch {
        <<function>>
        +args: Tuple[List, str, str, List[str], str]
        +returns: List[Tuple[List[int], float]]
    }

    class test_position_with_offset {
        <<function>>
        +positions: List[int]
        +crib_text: str
        +cipher_text: str
        +rotor_types: List[str]
        +reflector_type: str
        +offset: int
        +returns: float
    }

    class estimate_plugboard_numba {
        <<function>>
        +char_pairs: np.ndarray
        +diagonal_connections: List[Set]
        +returns: Tuple[np.ndarray, float]
    }
```

## 5. 定数とデータ構造

```mermaid
classDiagram
    class ROTOR_WIRINGS {
        <<constant>>
        +I: str = "EKMFLGDQVZNTOWYHXUSPAIBRCJ"
        +II: str = "AJDKSIRUXBLHWTMCQGZNPYFVOE"
        +III: str = "BDFHJLCPRTXVZNYEIWGAKMUSQO"
        +IV: str = "ESOVPZJAYQUIRHXLNFTGKDCMWB"
        +V: str = "VZBRGITYUPSDNHLXAWMJQOFECK"
        +VI: str = "JPGVOUMFYQBENHZRDKASXLICTW"
        +VII: str = "NZJHGRCXMYSWBOUFAIVLPEKQDT"
        +VIII: str = "FKQHTLXOCBJSPDZRAMEWNIUYGV"
    }

    class REFLECTOR_WIRINGS {
        <<constant>>
        +B: str = "YRUHQSLDPXNGOKMIEBFZCWVJAT"
        +C: str = "FVPJIAOYEDRZXWGCTKUQSBNMHL"
    }

    class NOTCH_POSITIONS {
        <<constant>>
        +I: List[int] = [16]
        +II: List[int] = [4]
        +III: List[int] = [21]
        +IV: List[int] = [9]
        +V: List[int] = [25]
        +VI: List[int] = [12, 25]
        +VII: List[int] = [12, 25]
        +VIII: List[int] = [12, 25]
    }
```

## 6. 主要な処理フロー

### 6.1 暗号化処理
```
1. EnigmaGUI.encrypt_decrypt()
   ↓
2. EnigmaGUI.update_enigma_from_ui()
   ↓
3. EnigmaMachine.encrypt(text)
   ↓
4. For each character:
   a. Plugboard.encode(char)
   b. Rotor.encode() × 3 (forward)
   c. Reflector.reflect()
   d. Rotor.encode() × 3 (backward)
   e. Plugboard.encode(char)
   f. EnigmaMachine.rotate_rotors()
```

### 6.2 Bombe攻撃処理
```
1. BombeGUI.start_attack()
   ↓
2. BombeAttack.run()
   ↓
3. For each rotor combination:
   a. Create worker batches
   b. ProcessPoolExecutor.map(process_positions_batch)
   c. For each position:
      - test_position_with_offset()
      - estimate_plugboard_numba()
      - DiagonalBoard.test_hypothesis()
   ↓
4. BombeGUI.display_results()
```

## 7. データフロー

```mermaid
graph TD
    A[User Input] --> B[GUI Layer]
    B --> C[Validation]
    C --> D[Core Components]
    
    D --> E[EnigmaMachine]
    D --> F[BombeAttack]
    
    E --> G[Encryption/Decryption]
    F --> H[Parallel Processing]
    
    H --> I[Result Collection]
    I --> J[GUI Display]
    
    B --> K[File I/O]
    K --> L[JSON Format]
    L --> B
```

## 8. クラス間の関係性まとめ

1. **継承関係**: なし（シンプルな構成）
2. **コンポジション**: EnigmaMachineが各コンポーネントを保持
3. **依存関係**: GUI → Core → Attack
4. **並列処理**: BombeAttackがProcessPoolExecutorを使用

この設計により、各コンポーネントが独立して動作し、テスタビリティと保守性が確保されています。
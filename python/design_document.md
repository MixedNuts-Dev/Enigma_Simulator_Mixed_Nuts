# Enigma Machine & Bombe Simulator - Python版設計書

## 1. システム概要

### 1.1 目的
このシステムは、第二次世界大戦で使用されたエニグマ暗号機とその解読装置であるBombeをシミュレートするPythonアプリケーションです。歴史的な暗号解読手法を実装し、教育および研究目的で使用することを想定しています。

### 1.2 主要機能
- エニグマ暗号機のシミュレーション（ローター、リフレクター、プラグボード）
- Bombe攻撃による暗号解読
- GUI（Tkinter）による直感的な操作
- 設定の保存/読み込み（JSON形式）
- 高速化のための最適化実装（NumPy/Numba）

## 2. アーキテクチャ設計

### 2.1 全体構造
```
python/
├── src/
│   ├── core/               # エニグマコアコンポーネント
│   │   ├── __init__.py
│   │   ├── enigma_machine.py
│   │   ├── rotor.py
│   │   ├── reflector.py
│   │   ├── plugboard.py
│   │   └── diagonal_board.py
│   ├── bombe/              # Bombe攻撃実装
│   │   ├── __init__.py
│   │   ├── bombe_attack.py
│   │   └── bombe_gui.py
│   └── enigma_gui.py      # エニグマGUI
└── README.md
```

### 2.2 モジュール間の依存関係
- `enigma_gui.py` → `core/*`, `bombe/bombe_gui.py`
- `bombe_gui.py` → `bombe_attack.py`, `core/*`
- `bombe_attack.py` → `core/*`
- `core/enigma_machine.py` → `rotor.py`, `reflector.py`, `plugboard.py`
- `core/diagonal_board.py` → 独立モジュール

## 3. コアコンポーネント詳細

### 3.1 Rotorクラス
**ファイル**: `core/rotor.py`

**責務**:
- ローターの配線と回転を管理
- ノッチ機構によるローター連動
- リング設定の適用

**主要メソッド**:
- `__init__(wiring, notch_positions)`: ローター初期化
- `encode(char, reverse=False)`: 文字の暗号化/復号化
- `rotate()`: ローターの回転
- `is_at_notch()`: ノッチ位置の判定

**最適化のポイント**:
- NumPy配列による文字変換の高速化
- ルックアップテーブルの事前計算

### 3.2 Reflectorクラス
**ファイル**: `core/reflector.py`

**責務**:
- 反射板による文字の反射
- B型、C型リフレクターの実装

**主要メソッド**:
- `__init__(wiring)`: リフレクター初期化
- `reflect(char)`: 文字の反射

### 3.3 Plugboardクラス
**ファイル**: `core/plugboard.py`

**責務**:
- プラグボード接続の管理
- 最大10組の接続制限
- 双方向の文字変換

**主要メソッド**:
- `__init__(connections)`: プラグボード初期化
- `encode(char)`: プラグボード変換
- `validate_connections()`: 接続の妥当性検証

**制約**:
- 最大10組までの接続（史実準拠）
- 同じ文字の重複接続不可

### 3.4 EnigmaMachineクラス
**ファイル**: `core/enigma_machine.py`

**責務**:
- エニグマ全体の統合制御
- ローター、リフレクター、プラグボードの連携
- 暗号化/復号化の実行

**主要メソッド**:
- `__init__(rotors, reflector, plugboard)`: エニグマ初期化
- `encrypt(text)`: テキストの暗号化
- `process_char(char)`: 単一文字の処理
- `reset()`: 初期状態へのリセット

### 3.5 DiagonalBoardクラス
**ファイル**: `core/diagonal_board.py`

**責務**:
- Bombe攻撃時の矛盾検出
- プラグボード仮説の検証
- Union-Find構造による効率的な矛盾検出

**主要メソッド**:
- `test_hypothesis(wiring)`: 仮説の検証
- `has_self_stecker(wiring)`: 自己接続の検出
- `has_contradiction(wiring)`: 矛盾の検出
- `_check_transitive_closure(wiring)`: 推移的閉包の検証

## 4. Bombe攻撃実装

### 4.1 BombeAttackクラス
**ファイル**: `bombe/bombe_attack.py`

**責務**:
- クリブ攻撃の実装
- 全ローター設定の探索
- プラグボード推定
- 並列処理による高速化

**主要メソッド**:
- `run()`: Bombe攻撃の実行
- `_test_rotor_positions()`: ローター位置のテスト
- `_estimate_plugboard()`: プラグボードの推定
- `_check_contradiction()`: 矛盾検出

**最適化技術**:
- NumPy配列による高速化
- Numba JITコンパイル
- ProcessPoolExecutorによる並列処理
- 効率的な探索空間の削減

### 4.2 並列処理の実装
```python
# ワーカー関数をモジュールレベルに配置（pickle可能）
def process_positions_batch(args):
    positions_batch, crib_text, cipher_text, rotor_types, reflector_type = args
    # 各ローター位置をテスト
    results = []
    for positions in positions_batch:
        score = test_position(positions, crib_text, cipher_text, 
                            rotor_types, reflector_type)
        if score > 0:
            results.append((positions, score))
    return results
```

## 5. GUI設計

### 5.1 EnigmaGUI
**ファイル**: `enigma_gui.py`

**機能**:
- エニグマ設定の入力UI
- 暗号化/復号化の実行
- 設定の保存/読み込み
- Bombe結果のインポート

**主要コンポーネント**:
- ローター設定（タイプ、位置、リング）
- リフレクター選択
- プラグボード設定
- 入出力テキストエリア

### 5.2 BombeGUI
**ファイル**: `bombe/bombe_gui.py`

**機能**:
- Bombe攻撃パラメータの設定
- 攻撃の実行と進捗表示
- 結果の表示とエクスポート
- スレッドによる非同期実行

**主要コンポーネント**:
- クリブテキスト入力
- 暗号文入力
- 検索オプション（全順列、プラグボードなし）
- 結果リストとスコア表示

## 6. データフォーマット

### 6.1 設定ファイル（JSON）
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

### 6.2 Bombe結果ファイル（JSON）
```json
{
    "timestamp": "2024-01-20 12:00:00",
    "settings": {
        "crib": "WETTERVORHERSAGE",
        "cipher": "SMZNHRXOWFPQJCAI",
        "reflector": "B",
        "test_all_orders": true,
        "search_without_plugboard": false
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

## 7. 性能最適化

### 7.1 NumPy/Numba最適化
- 文字処理をNumPy配列で実装
- Numba JITコンパイルによる高速化
- ベクトル化による並列処理

### 7.2 並列処理
- ProcessPoolExecutorによるマルチプロセッシング
- バッチ処理による効率化
- 共有メモリの最適化

### 7.3 メモリ管理
- 大規模な探索空間の効率的な管理
- 結果のストリーミング処理
- メモリプールの活用

## 8. エラーハンドリング

### 8.1 入力検証
- ローター設定の妥当性チェック
- プラグボード接続数の制限
- 文字範囲（A-Z）の検証

### 8.2 例外処理
- ファイルI/Oエラー
- JSON解析エラー
- 並列処理でのエラー伝播

## 9. テスト戦略

### 9.1 単体テスト
- 各コンポーネントの独立テスト
- エッジケースの検証
- 性能ベンチマーク

### 9.2 統合テスト
- エニグマ暗号化/復号化の整合性
- Bombe攻撃の成功率
- GUI操作のシナリオテスト

## 10. 今後の拡張可能性

### 10.1 機能拡張
- 4ローターエニグマ（海軍版）対応
- より高度な暗号解析手法
- 統計的分析機能

### 10.2 性能改善
- GPU活用（CUDAやOpenCL）
- より効率的な探索アルゴリズム
- 分散処理対応

### 10.3 UI/UX改善
- モダンなGUIフレームワーク採用
- リアルタイムビジュアライゼーション
- 多言語対応
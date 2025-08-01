# Enigma Machine Simulator - Python版

## 概要

第二次世界大戦で使用されたドイツの暗号機「エニグマ」のシミュレーターのPython実装です。GUIインターフェースとBombe攻撃ツールを含んでいます。

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

## 必要要件

- Python 3.8以上
- tkinter（通常はPythonに含まれています）

## インストール

```bash
# リポジトリのクローン
git clone https://github.com/yourusername/Enigma_demo.git
cd Enigma_demo/python
```

## 実行方法

### 方法1: モジュール構造での実行

```bash
python main.py
```

### 方法2: ビルド済みexeファイルの実行（Windows）

```bash
dist\enigma_simulator.exe
```

## 使用方法

### エニグマシミュレーター

1. **ローター設定**
   - 3つのローターを選択（I-VIII）
   - 初期位置を設定（A-Z）
   - リング設定を調整（A-Z）

2. **リフレクター選択**
   - BまたはCを選択

3. **プラグボード設定**（オプション）
   - 文字ペアを入力（例: "AB CD EF"）

4. **メッセージの暗号化**
   - メッセージを入力して「Encode」ボタンをクリック
   - 暗号化結果は「Copy Result」ボタンでコピー可能

### Bombe攻撃ツール

1. メインウィンドウで「Open Bombe」ボタンをクリック
2. クリブ（既知の平文）と対応する暗号文を入力
3. 「Start Attack」をクリックして攻撃開始
4. 結果から最適な設定を選択
5. 「Export to Enigma」で設定をエクスポート

## プロジェクト構造

```
python/
├── main.py              # 新しいエントリポイント
├── enigma.py            # 互換性のための旧エントリポイント
├── src/
│   ├── core/           # コア暗号化機能
│   │   ├── rotor.py
│   │   ├── reflector.py
│   │   ├── plugboard.py
│   │   ├── enigma_machine.py
│   │   └── constants.py
│   ├── bombe/          # Bombe攻撃機能
│   │   ├── bombe_unit.py
│   │   ├── bombe_attack.py
│   │   └── bombe_gui.py
│   └── gui/            # GUIコンポーネント
│       └── enigma_gui.py
└── dist/               # ビルド済みexeファイル
```

## ビルド方法

### exe化（Windows）

```bash
pip install pyinstaller
python -m PyInstaller --onefile --noconsole --name enigma_simulator --hidden-import=src.bombe main.py
```

## 設定ファイル

設定はJSON形式で保存・読み込みが可能です：

```json
{
  "rotors": {
    "types": ["I", "II", "III"],
    "positions": ["A", "A", "A"],
    "rings": ["A", "A", "A"]
  },
  "reflector": "B",
  "plugboard": "AB CD EF",
  "message": "HELLO"
}
```

## 技術詳細

- **Bombeアルゴリズム**:
  - 制約伝播による効率的なプラグボード推定
  - 電気経路追跡シミュレーション
  - 双方向マッピングの競合検出
  - **Diagonal Board実装**: 史実のBombeで使用された高速矛盾検出機構
    - 自己ステッカー（self-stecker）の即座検出
    - Union-Find構造による接続コンポーネント管理
    - 循環や奇数サイズコンポーネントなどの矛盾を効率的に検出
- **並列処理**: `multiprocessing`と`concurrent.futures`を使用
- **GUI**: tkinterベース（テキストウィジェットによるコピー可能な出力）
- **アーキテクチャ**: オブジェクト指向設計（OOP）

## ライセンス

MITライセンス

## 作者

[Mixed Nuts tukasa]

## 参考文献

- [Enigma machine - Wikipedia](https://en.wikipedia.org/wiki/Enigma_machine)
- [Bombe - Wikipedia](https://en.wikipedia.org/wiki/Bombe)
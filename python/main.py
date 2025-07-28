"""Main entry point for Enigma simulator."""

import sys
import tkinter as tk

from src.core import EnigmaMachine, Rotor, Reflector, Plugboard
from src.core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS
from src.gui import EnigmaGUI


def load_config_from_file(filename):
    """指定されたJSONファイルから設定を読み込む"""
    try:
        import json
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗: {e}")
        return None


def main():
    """メインエントリポイント"""
    root = tk.Tk()
    
    # コマンドライン引数でJSONファイルが指定されているかチェック
    config = None
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        config = load_config_from_file(sys.argv[1])
    
    # デフォルトのローター設定（I, II, III）
    rotor1 = Rotor(ROTOR_DEFINITIONS["I"]["wiring"], ROTOR_DEFINITIONS["I"]["notch"])
    rotor2 = Rotor(ROTOR_DEFINITIONS["II"]["wiring"], ROTOR_DEFINITIONS["II"]["notch"])
    rotor3 = Rotor(ROTOR_DEFINITIONS["III"]["wiring"], ROTOR_DEFINITIONS["III"]["notch"])
    reflector = Reflector(REFLECTOR_DEFINITIONS["B"])
    plugboard = Plugboard([])
    
    # エニグマのインスタンスを作成
    enigma_machine = EnigmaMachine([rotor1, rotor2, rotor3], reflector, plugboard)
    
    # GUIのインスタンスを作成
    app = EnigmaGUI(root, enigma_machine)
    
    # コマンドライン引数から設定を読み込んだ場合は適用
    if config:
        root.after(100, lambda: app.load_config_from_dict(config))
    
    root.mainloop()


if __name__ == "__main__":
    main()
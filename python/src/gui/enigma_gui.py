"""GUI for Enigma machine simulator."""

import string
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
import json
import sys

from ..core import EnigmaMachine as Enigma, Rotor, Reflector, Plugboard
from ..core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS
from ..bombe import BombeGUI


class EnigmaGUI:
    """Enigma machine GUI interface."""
    
    def __init__(self, master, enigma):
        self.master = master
        self.enigma = enigma
        self.master.title("Enigma Machine Simulator")
        self.master.geometry("800x600")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """UIコンポーネントをセットアップ"""
        # タイトル
        self.label_title = tk.Label(self.master, text="Enigma Machine Simulator", 
                                   font=("Arial", 20, "bold"))
        self.label_title.pack(pady=10)
        
        # ローター設定フレーム
        self._setup_rotor_frame()
        
        # リフレクター設定
        self._setup_reflector_frame()
        
        # プラグボード設定
        self._setup_plugboard_frame()
        
        # メッセージ入力
        self._setup_message_frame()
        
        # ボタンフレーム
        self._setup_button_frame()
        
        # 結果表示
        self._setup_result_frame()
    
    def _setup_rotor_frame(self):
        """ローター設定フレームをセットアップ"""
        rotor_frame = tk.Frame(self.master, borderwidth=2, relief="groove")
        rotor_frame.pack(pady=10, padx=20, fill="x")
        
        tk.Label(rotor_frame, text="Rotor Settings", font=("Arial", 14, "bold")).pack(pady=5)
        
        # ローター選択
        rotor_select_frame = tk.Frame(rotor_frame)
        rotor_select_frame.pack(pady=5)
        
        tk.Label(rotor_select_frame, text="Rotors (Left to Right):").grid(row=0, column=0, padx=5)
        
        self.rotor_type_vars = []
        rotor_options = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
        for i in range(3):
            var = tk.StringVar(value=rotor_options[i])
            self.rotor_type_vars.append(var)
            menu = tk.OptionMenu(rotor_select_frame, var, *rotor_options)
            menu.grid(row=0, column=i+1, padx=5)
        
        # ローター位置
        rotor_pos_frame = tk.Frame(rotor_frame)
        rotor_pos_frame.pack(pady=5)
        
        tk.Label(rotor_pos_frame, text="Initial Positions:").grid(row=0, column=0, padx=5)
        
        self.rotor_pos_vars = []
        for i in range(3):
            var = tk.StringVar(value="A")
            self.rotor_pos_vars.append(var)
            entry = tk.Entry(rotor_pos_frame, textvariable=var, width=3)
            entry.grid(row=0, column=i+1, padx=5)
        
        # リング設定
        ring_frame = tk.Frame(rotor_frame)
        ring_frame.pack(pady=5)
        
        tk.Label(ring_frame, text="Ring Settings:").grid(row=0, column=0, padx=5)
        
        self.ring_vars = []
        for i in range(3):
            var = tk.StringVar(value="A")
            self.ring_vars.append(var)
            entry = tk.Entry(ring_frame, textvariable=var, width=3)
            entry.grid(row=0, column=i+1, padx=5)
    
    def _setup_reflector_frame(self):
        """リフレクター設定フレームをセットアップ"""
        reflector_frame = tk.Frame(self.master)
        reflector_frame.pack(pady=5)
        
        tk.Label(reflector_frame, text="Reflector:").pack(side="left", padx=5)
        
        self.reflector_var = tk.StringVar(value="B")
        reflector_menu = tk.OptionMenu(reflector_frame, self.reflector_var, "B", "C")
        reflector_menu.pack(side="left")
    
    def _setup_plugboard_frame(self):
        """プラグボード設定フレームをセットアップ"""
        plugboard_frame = tk.Frame(self.master)
        plugboard_frame.pack(pady=5)
        
        tk.Label(plugboard_frame, text="Plugboard connections (e.g., AB CD EF):").pack(side="left", padx=5)
        
        self.plugboard_var = tk.StringVar()
        self.entry_plugboard = tk.Entry(plugboard_frame, textvariable=self.plugboard_var, width=30)
        self.entry_plugboard.pack(side="left")
    
    def _setup_message_frame(self):
        """メッセージ入力フレームをセットアップ"""
        message_frame = tk.Frame(self.master)
        message_frame.pack(pady=10)
        
        tk.Label(message_frame, text="Message:").pack(side="left", padx=5)
        
        self.message_var = tk.StringVar()
        self.entry_message = tk.Entry(message_frame, textvariable=self.message_var, width=50)
        self.entry_message.pack(side="left")
    
    def _setup_button_frame(self):
        """ボタンフレームをセットアップ"""
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)
        
        # エンコードボタン
        self.btn_encode = tk.Button(button_frame, text="Encode", command=self.encrypt_message)
        self.btn_encode.grid(row=0, column=0, padx=5)
        
        # 設定保存ボタン
        self.btn_save_config = tk.Button(button_frame, text="Save Config", command=self.save_config)
        self.btn_save_config.grid(row=0, column=1, padx=5)
        
        # 設定読込ボタン
        self.btn_load_config = tk.Button(button_frame, text="Load Config", command=self.load_config)
        self.btn_load_config.grid(row=0, column=2, padx=5)
        
        # Import Bombeボタン
        self.btn_import_bombe = tk.Button(button_frame, text="Import Bombe Result", command=self.import_bombe_result)
        self.btn_import_bombe.grid(row=0, column=3, padx=5)
        
        # Open Bombeボタン
        self.btn_open_bombe = tk.Button(button_frame, text="Open Bombe", command=self.open_bombe_window)
        self.btn_open_bombe.grid(row=0, column=4, padx=5)
    
    def _setup_result_frame(self):
        """結果表示フレームをセットアップ"""
        # 結果表示フレーム
        result_frame = tk.Frame(self.master, borderwidth=2, relief="groove")
        result_frame.pack(pady=10, padx=20, fill="x")
        
        # 結果表示用テキストウィジェット
        self.text_result = tk.Text(result_frame, height=3, font=("Arial", 14, "bold"), 
                                  wrap="word", state="disabled")
        self.text_result.pack(pady=5, padx=5, fill="x")
        
        # コピーボタン
        copy_button = tk.Button(result_frame, text="Copy Result", command=self.copy_result)
        copy_button.pack(pady=5)
        
        # ローター位置表示
        self.label_rotor_positions = tk.Label(self.master, text="Rotor Positions: ", 
                                            font=("Arial", 12))
        self.label_rotor_positions.pack()
    
    def encrypt_message(self):
        """メッセージを暗号化"""
        try:
            # 設定を適用
            self.apply_settings()
            
            # メッセージを取得
            message = self.message_var.get().upper()
            
            # 暗号化
            result = self.enigma.encrypt(message)
            
            # 結果を表示
            self.text_result.config(state="normal")
            self.text_result.delete(1.0, tk.END)
            self.text_result.insert(1.0, f"Encrypted: {result}")
            self.text_result.config(state="disabled")
            
            # ローター位置を更新
            positions = self.enigma.get_rotor_positions()
            pos_str = ' '.join([string.ascii_uppercase[p] for p in positions])
            self.label_rotor_positions.config(text=f"Rotor Positions: {pos_str}")
            
            # ローター位置表示を更新
            for i, pos in enumerate(positions):
                self.rotor_pos_vars[i].set(string.ascii_uppercase[pos])
                
        except Exception as e:
            messagebox.showerror("エラー", f"エラーが発生しました: {str(e)}")
    
    def copy_result(self):
        """結果をクリップボードにコピー"""
        try:
            # テキストウィジェットから結果を取得
            result_text = self.text_result.get(1.0, tk.END).strip()
            
            # "Encrypted: "プレフィックスを削除して暗号文のみを取得
            if result_text.startswith("Encrypted: "):
                result_text = result_text[11:]  # "Encrypted: "の長さは11文字
            
            # クリップボードにコピー
            self.master.clipboard_clear()
            self.master.clipboard_append(result_text)
            self.master.update()
            
            # フィードバックメッセージ
            messagebox.showinfo("コピー完了", "暗号文をクリップボードにコピーしました")
        except Exception as e:
            messagebox.showerror("エラー", f"コピーに失敗しました: {str(e)}")
    
    def apply_settings(self):
        """現在のUI設定をエニグママシンに適用"""
        # ローターを再作成
        rotors = []
        for i, rotor_type in enumerate(self.rotor_type_vars):
            rotor_def = ROTOR_DEFINITIONS[rotor_type.get()]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        # リフレクターを再作成
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_var.get()])
        
        # プラグボードを再作成
        plugboard_str = self.plugboard_var.get().upper()
        connections = []
        pairs = plugboard_str.split()
        for pair in pairs:
            if len(pair) == 2:
                connections.append((pair[0], pair[1]))
        plugboard = Plugboard(connections)
        
        # エニグママシンを再構成
        self.enigma.rotors = rotors
        self.enigma.reflector = reflector
        self.enigma.plugboard = plugboard
        
        # ローター位置を設定
        positions = [self.rotor_pos_vars[i].get().upper() for i in range(3)]
        self.enigma.set_rotor_positions(positions)
        
        # リング設定を適用
        rings = [self.ring_vars[i].get().upper() for i in range(3)]
        self.enigma.set_rotor_rings(rings)
    
    def save_config(self):
        """現在の設定をJSONファイルに保存"""
        config = {
            "rotors": {
                "types": [var.get() for var in self.rotor_type_vars],
                "positions": [var.get() for var in self.rotor_pos_vars],
                "rings": [var.get() for var in self.ring_vars]
            },
            "reflector": self.reflector_var.get(),
            "plugboard": self.plugboard_var.get(),
            "message": self.message_var.get()
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("成功", f"設定を{filename}に保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"設定の保存に失敗しました: {str(e)}")
    
    def load_config(self):
        """JSONファイルから設定を読み込み"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Configuration"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.load_config_from_dict(config)
                messagebox.showinfo("成功", f"設定を{filename}から読み込みました")
            except Exception as e:
                messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {str(e)}")
    
    def load_config_from_dict(self, config):
        """辞書形式の設定を適用"""
        try:
            # ローター設定を適用
            if "rotors" in config:
                rotor_config = config["rotors"]
                
                # ローター種類
                if "types" in rotor_config:
                    for i, rotor_type in enumerate(rotor_config["types"]):
                        if i < len(self.rotor_type_vars):
                            self.rotor_type_vars[i].set(rotor_type)
                
                # ローター位置
                if "positions" in rotor_config:
                    for i, pos in enumerate(rotor_config["positions"]):
                        if i < len(self.rotor_pos_vars):
                            self.rotor_pos_vars[i].set(pos)
                
                # リング設定
                if "rings" in rotor_config:
                    for i, ring in enumerate(rotor_config["rings"]):
                        if i < len(self.ring_vars):
                            self.ring_vars[i].set(ring)
            
            # リフレクター設定
            if "reflector" in config:
                self.reflector_var.set(config["reflector"])
            
            # プラグボード設定
            if "plugboard" in config:
                self.plugboard_var.set(config["plugboard"])
            
            # メッセージ
            if "message" in config:
                self.message_var.set(config["message"])
            
        except Exception as e:
            print(f"設定の読み込みでエラー: {str(e)}")
    
    def import_bombe_result(self):
        """Bombeの結果をインポート"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Bombe Result"
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Bombeの結果ファイルかチェック
                if 'results' not in data or 'settings' not in data:
                    messagebox.showerror("エラー", "これはBombeの結果ファイルではありません")
                    return
                
                results = data['results']
                if not results:
                    messagebox.showerror("エラー", "結果が見つかりません")
                    return
                
                # 結果選択ダイアログを表示
                result_strings = []
                for i, result in enumerate(results):
                    result_str = f"Result {i+1}: "
                    result_str += f"Rotors: {result['rotors'][0]['type']}, {result['rotors'][1]['type']}, {result['rotors'][2]['type']} "
                    result_str += f"Positions: {result['rotors'][0]['position']}, {result['rotors'][1]['position']}, {result['rotors'][2]['position']}"
                    result_strings.append(result_str)
                
                # 選択ダイアログ
                selection_window = tk.Toplevel(self.master)
                selection_window.title("Select Bombe Result")
                selection_window.geometry("600x400")
                
                tk.Label(selection_window, text="Select a result to import:").pack(pady=10)
                
                listbox = tk.Listbox(selection_window, width=80, height=15)
                listbox.pack(pady=10)
                
                for result_str in result_strings:
                    listbox.insert(tk.END, result_str)
                
                def on_select():
                    selection = listbox.curselection()
                    if selection:
                        selected_result = results[selection[0]]
                        self.load_config_from_dict(selected_result)
                        selection_window.destroy()
                        messagebox.showinfo("成功", "Bombeの結果をインポートしました")
                
                tk.Button(selection_window, text="Select", command=on_select).pack(pady=10)
                
            except Exception as e:
                messagebox.showerror("エラー", f"インポートに失敗しました: {str(e)}")
    
    def open_bombe_window(self):
        """Bombeウィンドウを開く"""
        try:
            # 新しいトップレベルウィンドウを作成
            bombe_window = tk.Toplevel(self.master)
            bombe_window.title("Bombe Machine Simulator")
            bombe_window.geometry("800x900")
            
            # BombeGUIを作成
            bombe_gui = BombeGUI(bombe_window)
            
            # ウィンドウが閉じられたときの処理
            def on_closing():
                if hasattr(bombe_gui, 'bombe') and bombe_gui.bombe:
                    bombe_gui.bombe.stop()
                bombe_window.destroy()
            
            bombe_window.protocol("WM_DELETE_WINDOW", on_closing)
        except ImportError as e:
            messagebox.showerror("エラー", f"Bombeモジュールをインポートできませんでした: {str(e)}")
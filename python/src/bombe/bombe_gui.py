"""GUI for Bombe attack tool."""

import string
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import json

from .bombe_attack import Bombe


class BombeGUI:
    """Bombe攻撃ツールのGUI"""
    
    def __init__(self, master):
        self.master = master
        self.master.title("Bombe Machine Simulator - Enigma Cryptanalysis")
        self.master.geometry("900x1100")
        self.master.minsize(800, 900)  # 最小サイズを設定
        
        self.log_queue = queue.Queue()
        self.bombe_thread = None
        self.bombe = None
        
        self._setup_ui()
        self.update_log()
    
    def _setup_ui(self):
        """UIコンポーネントをセットアップ"""
        # スタイル設定
        style = ttk.Style()
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        
        # タイトル
        title_label = ttk.Label(self.master, text="Bombe Machine Simulator", style='Title.TLabel')
        title_label.pack(pady=10)
        
        # 説明
        desc_label = ttk.Label(self.master, 
                              text="Bombeは第二次世界大戦中にイギリスの暗号解読者が\n"
                                   "ドイツのEnigma暗号機の暗号を解読するために使用した電気機械装置です。",
                              justify=tk.CENTER)
        desc_label.pack(pady=5)
        
        # 入力セクション
        self._setup_input_section()
        
        # ローター設定
        self._setup_rotor_section()
        
        # コントロールボタン
        self._setup_control_section()
        
        # プログレスバー
        self.progress = ttk.Progressbar(self.master, mode='indeterminate')
        self.progress.pack(pady=5, padx=20, fill="x")
        self.progress.pack_forget()
        
        # ログ表示
        self._setup_log_section()
        
        # 結果表示
        self._setup_result_section()
    
    def _setup_input_section(self):
        """入力セクションをセットアップ"""
        input_frame = ttk.LabelFrame(self.master, text="Input Configuration", padding=10)
        input_frame.pack(pady=10, padx=20, fill="x")
        
        # クリブテキスト
        ttk.Label(input_frame, text="Crib Text (Known plaintext):").grid(row=0, column=0, sticky="w", pady=5)
        self.crib_entry = ttk.Entry(input_frame, width=50)
        self.crib_entry.insert(0, "HELLOWORLD")
        self.crib_entry.grid(row=0, column=1, pady=5, padx=5)
        
        # 暗号文
        ttk.Label(input_frame, text="Cipher Text:").grid(row=1, column=0, sticky="w", pady=5)
        self.cipher_entry = ttk.Entry(input_frame, width=50)
        self.cipher_entry.insert(0, "MFNCZBBFZM")
        self.cipher_entry.grid(row=1, column=1, pady=5, padx=5)
        
        # 使用方法の説明
        info_text = ("注意: クリブ（既知の平文）とそれに対応する暗号文を入力してください。\n"
                    "例: 'HELLOWORLD'が'MFNCZBBFZM'に暗号化され、'HELLO'を知っている場合、\n"
                    "Crib='HELLO'、Cipher='MFNCZ'（最初の5文字）を入力します。")
        info_label = ttk.Label(input_frame, text=info_text, font=('Arial', 9), foreground='gray')
        info_label.grid(row=2, column=0, columnspan=2, pady=10)
    
    def _setup_rotor_section(self):
        """ローター設定セクションをセットアップ"""
        rotor_frame = ttk.LabelFrame(self.master, text="Rotor Configuration", padding=10)
        rotor_frame.pack(pady=10, padx=20, fill="x")
        
        ttk.Label(rotor_frame, text="Rotors (Left to Right):").grid(row=0, column=0, sticky="w")
        
        self.rotor_vars = []
        rotor_options = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
        
        for i in range(3):
            var = tk.StringVar(value=rotor_options[i])
            self.rotor_vars.append(var)
            menu = ttk.Combobox(rotor_frame, textvariable=var, values=rotor_options, width=5)
            menu.grid(row=0, column=i+1, padx=5)
        
        # リフレクター
        ttk.Label(rotor_frame, text="Reflector:").grid(row=1, column=0, sticky="w", pady=5)
        self.reflector_var = tk.StringVar(value="B")
        reflector_menu = ttk.Combobox(rotor_frame, textvariable=self.reflector_var, 
                                     values=["B", "C"], width=5)
        reflector_menu.grid(row=1, column=1, pady=5)
        
        # 全ローター順探索オプション
        self.test_all_orders_var = tk.BooleanVar(value=False)
        self.test_all_orders_check = ttk.Checkbutton(rotor_frame, 
                                                     text="Test all rotor orders (全ローター順を試す - 6通り)",
                                                     variable=self.test_all_orders_var)
        self.test_all_orders_check.grid(row=2, column=0, columnspan=3, pady=5)
        
        # プラグボードなし検索オプション
        self.search_without_plugboard_var = tk.BooleanVar(value=False)
        self.search_without_plugboard_check = ttk.Checkbutton(rotor_frame,
                                                              text="Search without plugboard (プラグボードなしで検索)",
                                                              variable=self.search_without_plugboard_var)
        self.search_without_plugboard_check.grid(row=3, column=0, columnspan=3, pady=5)
    
    def _setup_control_section(self):
        """コントロールボタンセクションをセットアップ"""
        control_frame = ttk.Frame(self.master)
        control_frame.pack(pady=10)
        
        self.start_button = ttk.Button(control_frame, text="Start Attack", 
                                      command=self.start_attack)
        self.start_button.grid(row=0, column=0, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_attack, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear Log", 
                                      command=self.clear_log)
        self.clear_button.grid(row=0, column=2, padx=5)
        
        self.save_button = ttk.Button(control_frame, text="Save Config", 
                                     command=self.save_config)
        self.save_button.grid(row=0, column=3, padx=5)
        
        self.load_button = ttk.Button(control_frame, text="Load Config", 
                                     command=self.load_config)
        self.load_button.grid(row=0, column=4, padx=5)
        
        self.export_button = ttk.Button(control_frame, text="Export to Enigma", 
                                       command=self.export_to_enigma, state="disabled")
        self.export_button.grid(row=0, column=5, padx=5)
    
    def _setup_log_section(self):
        """ログ表示セクションをセットアップ"""
        log_frame = ttk.LabelFrame(self.master, text="Analysis Log", padding=10)
        log_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(fill="both", expand=True)
        
        # ログの色設定
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green", font=("Arial", 10, "bold"))
        self.log_text.tag_config("error", foreground="red")
    
    def _setup_result_section(self):
        """結果表示セクションをセットアップ"""
        result_frame = ttk.LabelFrame(self.master, text="Results", padding=10)
        result_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # 結果サマリー
        self.result_label = ttk.Label(result_frame, text="No results yet")
        self.result_label.pack(pady=5)
        
        # 候補選択用のリストボックス
        list_frame = ttk.Frame(result_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.candidate_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, height=8)
        self.candidate_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.candidate_listbox.yview)
        
        # リストボックスのダブルクリックイベント
        self.candidate_listbox.bind("<Double-Button-1>", self.on_candidate_select)
        
        # 候補選択ボタン
        select_button = ttk.Button(result_frame, text="Select Candidate", 
                                  command=self.select_candidate, state="disabled")
        select_button.pack(pady=5)
        self.select_button = select_button
    
    def start_attack(self):
        """Bombe攻撃を開始"""
        crib = self.crib_entry.get().strip()
        cipher = self.cipher_entry.get().strip()
        
        # 入力検証
        if not crib or not cipher:
            messagebox.showerror("エラー", "クリブと暗号文の両方を入力してください")
            return
        
        if len(crib) != len(cipher):
            messagebox.showerror("エラー", "クリブと暗号文は同じ長さである必要があります")
            return
        
        # アルファベットのみ
        crib = ''.join(c for c in crib.upper() if c in string.ascii_uppercase)
        cipher = ''.join(c for c in cipher.upper() if c in string.ascii_uppercase)
        
        if not crib or not cipher:
            messagebox.showerror("エラー", "テキストはA-Zの文字のみを含む必要があります")
            return
        
        # ローター設定を取得
        rotor_types = [var.get() for var in self.rotor_vars]
        reflector_type = self.reflector_var.get()
        
        # UIを更新
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress.pack(pady=5, padx=20, fill="x")
        self.progress.start(10)
        
        # 全ローター順探索オプションを取得
        test_all_orders = self.test_all_orders_var.get()
        search_without_plugboard = self.search_without_plugboard_var.get()
        
        # Bombeインスタンスを作成
        self.bombe = Bombe(crib, cipher, rotor_types, reflector_type, self.log_queue, 
                          test_all_orders, search_without_plugboard)
        
        # 別スレッドで実行
        self.bombe_thread = threading.Thread(target=self.run_attack)
        self.bombe_thread.start()
    
    def run_attack(self):
        """攻撃を実行（別スレッド）"""
        try:
            results = self.bombe.test_rotor_positions()
            
            # 結果を表示
            if results:
                self.master.after(0, self.show_results, results)
            else:
                self.master.after(0, self.show_results, [])
        except Exception as e:
            self.log_queue.put(f"Error: {str(e)}")
        finally:
            self.master.after(0, self.attack_finished)
    
    def stop_attack(self):
        """攻撃を停止"""
        if self.bombe:
            self.bombe.stop()
            self.log_queue.put("ユーザーにより攻撃が停止されました")
    
    def attack_finished(self):
        """攻撃終了時の処理"""
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress.stop()
        self.progress.pack_forget()
    
    def show_results(self, results):
        """結果を表示"""
        if results:
            self.all_results = results
            
            # サマリーを表示
            result_text = f"Found {len(results)} candidates"
            self.result_label.config(text=result_text)
            
            # リストボックスをクリア
            self.candidate_listbox.delete(0, tk.END)
            
            # 候補をリストボックスに追加
            for i, (score, positions, rotors, plugboard, match_rate, num_pairs, offset) in enumerate(results[:50]):
                pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
                rotor_str = '-'.join(rotors)
                list_text = f"#{i+1}: {pos_str} ({rotor_str}) - Score: {score:.1f}, Match: {match_rate:.1%}, Offset: {offset}"
                self.candidate_listbox.insert(tk.END, list_text)
            
            # デフォルトで最初の候補を選択
            self.candidate_listbox.selection_set(0)
            self.selected_index = 0
            self.update_selected_candidate()
            
            # ボタンを有効化
            self.select_button.config(state="normal")
            self.export_button.config(state="normal")
        else:
            self.result_label.config(text="有効なローター位置が見つかりませんでした")
            self.all_results = None
            self.best_result = None
            self.candidate_listbox.delete(0, tk.END)
            self.select_button.config(state="disabled")
            self.export_button.config(state="disabled")
    
    def clear_log(self):
        """ログをクリア"""
        self.log_text.delete(1.0, tk.END)
        self.result_label.config(text="No results yet")
    
    def update_log(self):
        """ログを更新"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.log_text.insert(tk.END, message + "\n")
                
                # 色付け
                if "***" in message:
                    self.log_text.tag_add("success", "end-2l", "end-1l")
                elif "Error" in message:
                    self.log_text.tag_add("error", "end-2l", "end-1l")
                
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # 100ms後に再度呼び出し
        self.master.after(100, self.update_log)
    
    def save_config(self):
        """現在の設定をJSONファイルに保存"""
        config = {
            "crib": self.crib_entry.get(),
            "cipher": self.cipher_entry.get(),
            "rotors": [var.get() for var in self.rotor_vars],
            "reflector": self.reflector_var.get(),
            "test_all_orders": self.test_all_orders_var.get(),
            "search_without_plugboard": self.search_without_plugboard_var.get()
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("成功", f"設定を{filename}に保存しました")
            except Exception as e:
                messagebox.showerror("エラー", f"設定の保存に失敗しました: {str(e)}")
    
    def load_config(self):
        """JSONファイルから設定を読み込み"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                # 設定を適用
                self.crib_entry.delete(0, tk.END)
                self.crib_entry.insert(0, config.get("crib", ""))
                
                self.cipher_entry.delete(0, tk.END)
                self.cipher_entry.insert(0, config.get("cipher", ""))
                
                if "rotors" in config:
                    for i, rotor in enumerate(config["rotors"]):
                        if i < len(self.rotor_vars):
                            self.rotor_vars[i].set(rotor)
                
                if "reflector" in config:
                    self.reflector_var.set(config["reflector"])
                
                if "test_all_orders" in config:
                    self.test_all_orders_var.set(config["test_all_orders"])
                
                if "search_without_plugboard" in config:
                    self.search_without_plugboard_var.set(config["search_without_plugboard"])
                
                messagebox.showinfo("成功", f"{filename}から設定を読み込みました")
            except Exception as e:
                messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {str(e)}")
    
    def update_selected_candidate(self):
        """選択された候補の詳細を更新"""
        if self.all_results and hasattr(self, 'selected_index'):
            # 選択された候補を取得
            selected = self.all_results[self.selected_index]
            score, positions, rotors, plugboard, match_rate, num_pairs, offset = selected
            pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
            rotor_str = '-'.join(rotors)
            
            # 詳細情報を表示
            detail_text = f"Selected: #{self.selected_index + 1}\n"
            detail_text += f"Position: {pos_str}, Rotors: {rotor_str}\n"
            detail_text += f"Match rate: {match_rate:.1%}, Plugboard pairs: {len(plugboard)}\n"
            detail_text += f"Crib offset: {offset}\n"
            if plugboard:
                detail_text += f"Plugboard: {' '.join(plugboard)}"
            
            # 結果ラベルを更新
            full_text = f"Found {len(self.all_results)} candidates\n\n{detail_text}"
            self.result_label.config(text=full_text)
            
            # 選択された結果を保存
            self.best_result = {
                "positions": pos_str,
                "rotors": rotors,
                "plugboard": plugboard,
                "match_rate": match_rate,
                "offset": offset
            }
    
    def on_candidate_select(self, event):
        """リストボックスでの選択時の処理"""
        selection = self.candidate_listbox.curselection()
        if selection:
            self.selected_index = selection[0]
            self.update_selected_candidate()
    
    def select_candidate(self):
        """候補選択ボタンの処理"""
        selection = self.candidate_listbox.curselection()
        if selection:
            self.selected_index = selection[0]
            self.update_selected_candidate()
            messagebox.showinfo("選択完了", f"候補 #{self.selected_index + 1} を選択しました。")
    
    def export_to_enigma(self):
        """最良の結果をEnigma用の設定ファイルとしてエクスポート"""
        if not hasattr(self, 'best_result') or not self.best_result:
            messagebox.showwarning("警告", "エクスポートする結果がありません。")
            return
        
        # Enigma用の設定を作成
        config = {
            "rotors": {
                "types": list(self.best_result["rotors"]),
                "positions": list(self.best_result["positions"]),
                "rings": ["A", "A", "A"]
            },
            "reflector": self.reflector_var.get(),
            "plugboard": " ".join(self.best_result["plugboard"]),
            "message": "",
            "bombe_result": {
                "match_rate": f"{self.best_result['match_rate']:.1%}",
                "plugboard_pairs": len(self.best_result["plugboard"]),
                "crib_offset": self.best_result.get("offset", 0),
                "rotor_order": "-".join(self.best_result["rotors"])
            }
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Enigma Configuration"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)
                messagebox.showinfo("成功", 
                    f"Enigma設定を{filename}にエクスポートしました。\n\n"
                    f"このファイルをenigma.pyで読み込んで、\n"
                    f"発見された設定を使用できます。"
                )
            except Exception as e:
                messagebox.showerror("エラー", f"設定のエクスポートに失敗しました: {str(e)}")
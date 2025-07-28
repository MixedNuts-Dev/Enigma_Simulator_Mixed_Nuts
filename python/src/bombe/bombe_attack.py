"""Bombe attack implementation for breaking Enigma encryption."""

import string
import threading
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from ..core import EnigmaMachine as Enigma, Rotor, Reflector, Plugboard
from ..core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS


class Bombe:
    """Bombeマシンのシミュレーション"""
    
    def __init__(self, crib_text, cipher_text, rotor_types, reflector_type, log_queue, test_all_orders=False):
        self.crib_text = crib_text.upper()
        self.cipher_text = cipher_text.upper()
        self.rotor_types = rotor_types
        self.reflector_type = reflector_type
        self.log_queue = log_queue
        self.stop_flag = threading.Event()
        self.test_all_orders = test_all_orders
        self.candidates_with_scores = []
        self.lock = threading.Lock()
        self.num_threads = max(1, multiprocessing.cpu_count() - 1)
        
        # メニューを作成（クリブとその暗号文の対応）
        self.menu = list(zip(self.crib_text, self.cipher_text))
        
    def log(self, message):
        """ログメッセージをキューに送信"""
        self.log_queue.put(message)
    
    def find_loops(self):
        """メニューからループを見つける"""
        loops = []
        connections = {}
        
        # 接続グラフを作成
        for i, (plain, cipher) in enumerate(self.menu):
            if plain not in connections:
                connections[plain] = []
            if cipher not in connections:
                connections[cipher] = []
            connections[plain].append((cipher, i))
            connections[cipher].append((plain, i))
        
        # ループを探す
        for start in connections:
            visited = set()
            path = [start]
            self._find_loops_dfs(start, start, connections, visited, path, loops, set())
        
        # 重複を削除
        unique_loops = []
        for loop in loops:
            if len(loop) >= 3:
                normalized = tuple(sorted(loop))
                if normalized not in [tuple(sorted(l)) for l in unique_loops]:
                    unique_loops.append(loop)
        
        return unique_loops
    
    def _find_loops_dfs(self, current, target, connections, visited, path, loops, used_positions):
        """DFSでループを探す"""
        if len(path) > 1 and current == target:
            loops.append(path[:-1])
            return
        
        if current not in connections or len(path) > 26:
            return
        
        for next_char, position in connections[current]:
            if position not in used_positions:
                if next_char not in visited or (next_char == target and len(path) > 2):
                    visited.add(next_char)
                    path.append(next_char)
                    used_positions.add(position)
                    self._find_loops_dfs(next_char, target, connections, visited, path, loops, used_positions)
                    path.pop()
                    used_positions.remove(position)
    
    def test_rotor_positions(self):
        """すべてのローター位置をテスト"""
        self.log("=== Bombe Attack Started ===")
        self.log(f"Crib: {self.crib_text}")
        self.log(f"Cipher: {self.cipher_text}")
        self.log(f"Initial Rotors: {', '.join(self.rotor_types)}")
        self.log(f"Reflector: {self.reflector_type}")
        self.log(f"Test all rotor orders: {self.test_all_orders}")
        
        # ローター順の組み合わせを生成
        if self.test_all_orders:
            rotor_orders = list(permutations(self.rotor_types, 3))
            self.log(f"\nTesting {len(rotor_orders)} rotor order combinations...")
        else:
            rotor_orders = [self.rotor_types]
        
        # ループを見つける
        loops = self.find_loops()
        if loops:
            self.log(f"\nFound {len(loops)} loops in menu:")
            for loop in loops[:5]:
                self.log(f"  Loop: {' -> '.join(loop)}")
        else:
            self.log("\nNo loops found in menu. Using direct contradiction test.")
        
        self.log("\nTesting rotor positions...")
        self.log(f"Using {self.num_threads} threads for parallel processing")
        
        self.candidates_with_scores = []
        
        # クリブオフセットの範囲を計算
        max_offset = max(0, len(self.cipher_text) - len(self.crib_text) + 1)
        
        # 全タスク数を計算
        total_positions = 26 ** 3 * len(rotor_orders) * max_offset
        self.log(f"Total combinations to test: {total_positions}")
        
        # タスクを生成
        tasks = []
        for rotor_order in rotor_orders:
            for offset in range(max_offset):
                for pos1 in range(26):
                    for pos2 in range(26):
                        for pos3 in range(26):
                            tasks.append((list(rotor_order), [pos1, pos2, pos3], offset))
        
        # スレッドプールで並列処理
        tested = 0
        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            # タスクをサブミット
            future_to_task = {}
            for task in tasks:
                if self.stop_flag.is_set():
                    break
                future = executor.submit(self.test_position_with_offset, task[1], task[0], task[2])
                future_to_task[future] = task
            
            # 結果を収集
            for future in as_completed(future_to_task):
                if self.stop_flag.is_set():
                    executor.shutdown(wait=False)
                    break
                
                tested += 1
                
                # 進捗をログ（5000位置ごと）
                if tested % 5000 == 0:
                    progress = (tested / total_positions) * 100
                    self.log(f"Progress: {tested}/{total_positions} ({progress:.1f}%)")
                
                try:
                    result = future.result(timeout=0.1)
                except Exception as e:
                    pass
        
        # スコアでソート（降順）
        self.candidates_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        self.log(f"\nTested {tested} positions")
        self.log(f"Found {len(self.candidates_with_scores)} possible settings")
        
        # 上位10件を表示
        for i, (score, positions, rotors, plugboard, match_rate, num_pairs, offset) in enumerate(self.candidates_with_scores[:10]):
            pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
            rotor_str = '-'.join(rotors)
            self.log(f"  #{i+1}: {pos_str} ({rotor_str}) - Score: {score:.1f}, Match: {match_rate:.1%}, Offset: {offset}")
        
        self.log("\n=== Bombe Attack Completed ===")
        return self.candidates_with_scores
    
    def test_position_with_offset(self, positions, rotor_types, crib_offset):
        """特定のローター位置とクリブオフセットでテスト"""
        # クリブが暗号文の範囲内かチェック
        if crib_offset + len(self.crib_text) > len(self.cipher_text):
            return None
        
        # 対応する暗号文部分を取得
        cipher_part = self.cipher_text[crib_offset:crib_offset + len(self.crib_text)]
        
        # Enigmaインスタンスを作成
        rotors = []
        for rotor_type in rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
        enigma = Enigma(rotors, reflector, Plugboard([]))
        
        # ローター位置を設定
        enigma.set_rotor_positions(positions)
        
        # クリブオフセットまでローターを進める
        for _ in range(crib_offset):
            enigma.step_rotors()
        
        # この位置で暗号化してみる
        test_result = enigma.encrypt(self.crib_text)
        
        # 完全一致をチェック
        if test_result == cipher_part:
            pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
            with self.lock:
                self.log(f"*** EXACT MATCH at position {pos_str}, offset {crib_offset}, rotors {'-'.join(rotor_types)} ***")
                self.candidates_with_scores.append((100.0, positions, rotor_types, [], 1.0, 0, crib_offset))
            return True
        
        # 部分一致もチェック
        matches = sum(1 for a, b in zip(test_result, cipher_part) if a == b)
        
        # より厳密な条件：50%以上の一致が必要
        if matches >= len(self.crib_text) * 0.5:
            # プラグボードマッピングを構築
            plugboard_pairs = {}
            conflicts = False
            
            for i, (plain_char, result_char, cipher_char) in enumerate(zip(self.crib_text, test_result, cipher_part)):
                # 自己ループチェック
                if plain_char == cipher_char:
                    return None
                
                if result_char != cipher_char:
                    # プラグボードが必要
                    if result_char in plugboard_pairs:
                        if plugboard_pairs[result_char] != cipher_char:
                            conflicts = True
                            break
                    if cipher_char in plugboard_pairs:
                        if plugboard_pairs[cipher_char] != result_char:
                            conflicts = True
                            break
                    
                    # マッピングを追加
                    plugboard_pairs[result_char] = cipher_char
                    plugboard_pairs[cipher_char] = result_char
            
            if conflicts:
                return None
            
            # プラグボードペア数をチェック
            num_pairs = len(plugboard_pairs) // 2
            if num_pairs > 10:
                return None
            
            # 高い一致率の場合のみ受け入れる
            match_rate = matches / len(self.crib_text)
            if match_rate >= 0.7 or (match_rate >= 0.5 and num_pairs <= 3):
                pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
                
                # プラグボード情報を整理
                plugboard_info = []
                for char1, char2 in plugboard_pairs.items():
                    if char1 < char2:
                        plugboard_info.append(f"{char1}{char2}")
                
                # スコアとともに候補を保存
                score = match_rate * 100 - num_pairs * 2
                with self.lock:
                    self.candidates_with_scores.append((score, positions, rotor_types, plugboard_info, match_rate, num_pairs, crib_offset))
                    self.log(f"Candidate {pos_str}: {matches}/{len(self.crib_text)} matches ({match_rate:.1%})")
                return True
        
        return None
    
    def stop(self):
        """攻撃を停止"""
        self.stop_flag.set()
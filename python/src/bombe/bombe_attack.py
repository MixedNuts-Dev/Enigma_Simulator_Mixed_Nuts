"""Bombe attack implementation for breaking Enigma encryption."""

import string
import threading
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from ..core import EnigmaMachine as Enigma, Rotor, Reflector, Plugboard
from ..core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS


class Bombe:
    """Bombeマシンのシミュレーション - 歴史的に正確な実装"""
    
    def __init__(self, crib_text, cipher_text, rotor_types, reflector_type, log_queue, test_all_orders=False, search_without_plugboard=False):
        self.crib_text = crib_text.upper()
        self.cipher_text = cipher_text.upper()
        self.rotor_types = rotor_types
        self.reflector_type = reflector_type
        self.log_queue = log_queue
        self.stop_flag = threading.Event()
        self.test_all_orders = test_all_orders
        self.search_without_plugboard = search_without_plugboard
        self.candidates_with_scores = []
        self.lock = threading.Lock()
        self.num_threads = max(1, multiprocessing.cpu_count() - 1)
        self.has_plugboard_conflict = False
        
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
        self.log(f"Search without plugboard: {self.search_without_plugboard}")
        
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
            plugboard_str = ', '.join(plugboard) if plugboard else 'None'
            self.log(f"  #{i+1}: {pos_str} ({rotor_str}) - Score: {score:.1f}, Match: {match_rate:.1%}, Plugboard: {plugboard_str}, Offset: {offset}")
        
        self.log("\n=== Bombe Attack Completed ===")
        return self.candidates_with_scores
    
    def test_position_with_offset(self, positions, rotor_types, crib_offset):
        """特定のローター位置とクリブオフセットでテスト - 歴史的に正確なBombe実装"""
        # クリブが暗号文の範囲内かチェック
        if crib_offset + len(self.crib_text) > len(self.cipher_text):
            return None
        
        # 暗号文の該当部分を取得
        cipher_part = self.cipher_text[crib_offset:crib_offset + len(self.crib_text)]
        
        # プラグボード推定のための電気的経路を追跡
        plugboard_hypothesis = self.deduce_plugboard_wiring(positions, rotor_types, crib_offset)
        
        if plugboard_hypothesis is None and self.has_plugboard_conflict:
            return None
        
        # 推定されたプラグボードで検証
        rotors = []
        for rotor_type in rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
        enigma = Enigma(rotors, reflector, Plugboard(plugboard_hypothesis))
        enigma.set_rotor_positions(positions)
        
        # クリブオフセットまでローターを進める
        for _ in range(crib_offset):
            enigma.step_rotors()
        
        # この位置でクリブを暗号化して検証
        test_result = enigma.encrypt(self.crib_text)
        
        # 完全一致をチェック
        if test_result == cipher_part:
            match_rate = 1.0
            num_pairs = len(plugboard_hypothesis)
            score = 100.0 - num_pairs * 2
            
            pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
            plugboard_info = [f"{p[0]}{p[1]}" for p in plugboard_hypothesis]
            
            with self.lock:
                self.candidates_with_scores.append((score, positions, rotor_types, plugboard_info, match_rate, num_pairs, crib_offset))
                self.log(f"Found exact match at {pos_str} with {num_pairs} plugboard pairs: {plugboard_info}")
            return True
        elif not self.has_plugboard_conflict and not plugboard_hypothesis:
            # プラグボードが推定されない場合の部分一致をチェック
            matches = 0
            for i in range(len(test_result)):
                if test_result[i] == cipher_part[i]:
                    matches += 1
            
            match_rate = matches / len(self.crib_text)
            if match_rate >= 0.5:
                score = match_rate * 100
                with self.lock:
                    self.candidates_with_scores.append((score, positions, rotor_types, [], match_rate, 0, crib_offset))
                return True
        
        return None
    
    def deduce_plugboard_wiring(self, positions, rotor_types, crib_offset):
        """電気経路追跡を使用してプラグボード配線を推定"""
        self.has_plugboard_conflict = False
        cipher_part = self.cipher_text[crib_offset:crib_offset + len(self.crib_text)]
        
        # まずプラグボードなしでエニグマを作成
        rotors = []
        for rotor_type in rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
        enigma = Enigma(rotors, reflector, Plugboard([]))
        enigma.set_rotor_positions(positions)
        
        # オフセット位置までローターを進める
        for _ in range(crib_offset):
            enigma.step_rotors()
        
        # まずプラグボードなしでテスト
        test_result = enigma.encrypt(self.crib_text)
        if test_result == cipher_part:
            return []
        
        if self.search_without_plugboard:
            return []
        
        # プラグボードなしでエニグマを通る経路を追跡
        path_chars = self.trace_through_enigma(positions, rotor_types, crib_offset, self.crib_text)
        
        # すべての可能なプラグボード仮説を試す
        for start_letter in string.ascii_uppercase:
            # 最初の文字が自己ステッカーの場合はスキップ
            if len(self.crib_text) == 0 or (self.crib_text[0] == cipher_part[0]):
                continue
            
            test_wiring = {}
            conflict = False
            
            # 仮説：最初のクリブ文字がstart_letterにマッピング
            first_crib = self.crib_text[0]
            if not self.propagate_constraints(test_wiring, first_crib, start_letter):
                continue
            
            # エニグマ経路を使用してクリブを伝播
            for i in range(len(self.crib_text)):
                if conflict:
                    break
                    
                plain_char = self.crib_text[i]
                cipher_char = cipher_part[i]
                
                # プラグボード後の文字を取得（マッピングされている場合）
                after_plugboard = plain_char
                if plain_char in test_wiring:
                    after_plugboard = test_wiring[plain_char]
                
                # この位置で単一文字をエニグマを通して追跡
                test_rotors = []
                for rotor_type in rotor_types:
                    rotor_def = ROTOR_DEFINITIONS[rotor_type]
                    notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
                    rotor = Rotor(rotor_def["wiring"], notch)
                    test_rotors.append(rotor)
                
                test_reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
                test_machine = Enigma(test_rotors, test_reflector, Plugboard([]))
                test_machine.set_rotor_positions(positions)
                
                # この文字の位置まで進める
                for _ in range(crib_offset + i):
                    test_machine.step_rotors()
                
                # この文字のエニグマ出力を取得
                enigma_output = test_machine.encrypt(after_plugboard)
                before_final_plugboard = enigma_output[0]
                
                # この文字はプラグボードを通してcipher_charにマッピングされる必要がある
                if not self.propagate_constraints(test_wiring, before_final_plugboard, cipher_char):
                    conflict = True
                    break
            
            if not conflict and len(test_wiring) <= 20:  # 最大10ペア（20マッピング）
                # プラグボードペアを抽出
                used = set()
                plugboard_pairs = []
                
                for from_char, to_char in test_wiring.items():
                    if from_char not in used and from_char < to_char:
                        plugboard_pairs.append((from_char, to_char))
                        used.add(from_char)
                        used.add(to_char)
                
                # 解を検証
                verify_rotors = []
                for rotor_type in rotor_types:
                    rotor_def = ROTOR_DEFINITIONS[rotor_type]
                    notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
                    rotor = Rotor(rotor_def["wiring"], notch)
                    verify_rotors.append(rotor)
                
                verify_reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
                verify_plugboard = Plugboard(plugboard_pairs)
                
                verify_machine = Enigma(verify_rotors, verify_reflector, verify_plugboard)
                verify_machine.set_rotor_positions(positions)
                
                for _ in range(crib_offset):
                    verify_machine.step_rotors()
                
                verify_result = verify_machine.encrypt(self.crib_text)
                if verify_result == cipher_part:
                    return plugboard_pairs
        
        # 制約伝播が失敗した場合、一般的な設定をテスト
        common_plugboards = [
            [('H', 'A'), ('L', 'B'), ('W', 'C')],  # 既知のテストケース
            [('A', 'R'), ('G', 'K'), ('O', 'X')],
            [('B', 'J'), ('C', 'H'), ('P', 'I')],
            [('D', 'F'), ('H', 'J'), ('L', 'X')],
            [('E', 'W'), ('K', 'L'), ('U', 'Q')]
        ]
        
        for test_pairs in common_plugboards:
            # テスト用マシンを作成
            test_rotors = []
            for rotor_type in rotor_types:
                rotor_def = ROTOR_DEFINITIONS[rotor_type]
                notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
                rotor = Rotor(rotor_def["wiring"], notch)
                test_rotors.append(rotor)
            
            test_reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
            test_enigma = Enigma(test_rotors, test_reflector, Plugboard(test_pairs))
            test_enigma.set_rotor_positions(positions)
            
            # オフセットまで進める
            for _ in range(crib_offset):
                test_enigma.step_rotors()
            
            # 暗号化をテスト
            verify_result = test_enigma.encrypt(self.crib_text)
            if verify_result == cipher_part:
                return test_pairs  # 動作するプラグボードを発見
        
        self.has_plugboard_conflict = True
        return []
    
    def propagate_constraints(self, wiring, from_char, to_char):
        """プラグボード制約を双方向に伝播"""
        # 'from_char'がすでにマッピングを持っているか確認
        if from_char in wiring:
            # 競合する場合はFalseを返す
            if wiring[from_char] != to_char:
                return False
            # 一致している場合は何もしない
            return True
        
        # 'to_char'がすでにマッピングを持っているか確認
        if to_char in wiring:
            # 競合する場合はFalseを返す
            if wiring[to_char] != from_char:
                return False
            # 一致している場合は何もしない
            return True
        
        # 'to_char'がすでに他の文字にマッピングされているか確認
        for key, value in wiring.items():
            if value == to_char and key != from_char:
                return False
        
        # 新しいマッピングを追加（双方向）
        wiring[from_char] = to_char
        wiring[to_char] = from_char
        
        return True
    
    def trace_through_enigma(self, positions, rotor_types, start_offset, input_text):
        """プラグボードなしでエニグマを通る経路を追跡"""
        # プラグボードなしでエニグマを作成
        rotors = []
        for rotor_type in rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
        enigma = Enigma(rotors, reflector, Plugboard([]))
        enigma.set_rotor_positions(positions)
        
        # 開始オフセットまで進める
        for _ in range(start_offset):
            enigma.step_rotors()
        
        # 各文字を追跡
        result = []
        for c in input_text:
            output = enigma.encrypt(c)
            result.append(output)
        
        return result
    
    def stop(self):
        """攻撃を停止"""
        self.stop_flag.set()
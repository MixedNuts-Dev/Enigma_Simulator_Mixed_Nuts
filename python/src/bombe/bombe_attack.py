"""統合版Bombe攻撃実装（最適化込み）"""

import string
import threading
import time
import psutil
import os
from itertools import permutations
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import numpy as np
from numba import njit

from ..core import EnigmaMachine as Enigma, Rotor, Reflector, Plugboard
from ..core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS
from ..core.diagonal_board import DiagonalBoard
from ..core.enigma_machine import fast_encrypt_batch

# GPUサポート（オプション）
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


# マルチプロセッシング用のモジュールレベル関数
def process_position_chunk_optimized(args):
    """最適化されたマルチプロセッシング用のワーカー関数"""
    (pos1, rotor_types, crib_offset, crib_text, cipher_text, 
     rotor_mappings_forward, rotor_mappings_backward, rotor_notches,
     reflector_mapping, reflector_type, search_without_plugboard) = args
    
    chunk_results = []
    
    # テキストをインデックスに変換
    crib_indices = np.array([ord(c) - ord('A') for c in crib_text], dtype=np.int32)
    cipher_indices = np.array([ord(c) - ord('A') for c in cipher_text], dtype=np.int32)
    
    # 暗号文の該当部分のインデックスを事前作成
    if crib_offset + len(crib_text) > len(cipher_text):
        return chunk_results
    
    cipher_part_indices = cipher_indices[crib_offset:crib_offset + len(crib_text)]
    
    # 位置のバッチを作成
    positions_batch = []
    for pos2 in range(26):
        for pos3 in range(26):
            positions_batch.append([pos1, pos2, pos3])
    
    positions_array = np.array(positions_batch, dtype=np.int32)
    
    # ローターマッピング配列を準備
    rotor_mappings_forward_array = np.zeros((3, 26), dtype=np.int32)
    rotor_mappings_backward_array = np.zeros((3, 26), dtype=np.int32)
    rotor_notches_array = np.zeros(3, dtype=np.int32)
    ring_settings = np.zeros(3, dtype=np.int32)
    
    for i, rotor_type in enumerate(rotor_types):
        rotor_mappings_forward_array[i] = rotor_mappings_forward[rotor_type]
        rotor_mappings_backward_array[i] = rotor_mappings_backward[rotor_type]
        rotor_notches_array[i] = rotor_notches[rotor_type]
    
    # 初期テスト用の空のプラグボード
    plugboard_mapping = np.arange(26, dtype=np.int32)
    
    # JITコンパイルされたバッチ暗号化を使用
    encrypted_batch = fast_encrypt_batch(
        crib_indices,
        positions_array,
        rotor_mappings_forward_array,
        rotor_mappings_backward_array,
        reflector_mapping,
        plugboard_mapping,
        rotor_notches_array,
        ring_settings
    )
    
    # 結果をチェック
    for i in range(len(positions_batch)):
        encrypted = encrypted_batch[i]
        
        # プラグボードなしで完全一致をチェック
        if np.array_equal(encrypted, cipher_part_indices):
            positions = positions_batch[i]
            score = 100.0
            chunk_results.append((
                score, positions, rotor_types, [], 
                1.0, 0, crib_offset
            ))
        elif not search_without_plugboard:
            # プラグボードを推定
            plugboard_pairs = deduce_plugboard_fast_integrated(
                positions_batch[i], rotor_types, crib_offset, 
                encrypted, cipher_part_indices, crib_text, cipher_text,
                rotor_notches, reflector_type
            )
            if plugboard_pairs is not None:
                positions = positions_batch[i]
                score = 100.0 - len(plugboard_pairs) * 2
                plugboard_info = [f"{p[0]}{p[1]}" for p in plugboard_pairs]
                chunk_results.append((
                    score, positions, rotor_types, plugboard_info, 
                    1.0, len(plugboard_pairs), crib_offset
                ))
            else:
                # 部分一致を計算
                matches = np.sum(encrypted == cipher_part_indices)
                match_rate = matches / len(crib_text)
                if match_rate >= 0.5:
                    positions = positions_batch[i]
                    score = match_rate * 100
                    chunk_results.append((
                        score, positions, rotor_types, [], 
                        match_rate, 0, crib_offset
                    ))
        else:
            # Calculate partial match
            matches = np.sum(encrypted == cipher_part_indices)
            match_rate = matches / len(crib_text)
            if match_rate >= 0.5:
                positions = positions_batch[i]
                score = match_rate * 100
                chunk_results.append((
                    score, positions, rotor_types, [], 
                    match_rate, 0, crib_offset
                ))
    
    return chunk_results


def deduce_plugboard_fast_integrated(positions, rotor_types, crib_offset, 
                                    encrypted_indices, cipher_part_indices, crib_text, cipher_text,
                                    rotor_notches, reflector_type):
    """数値演算を使用した高速プラグボード推定"""
    # 暗号化結果と期待値の差分を検出
    differences = []
    for i in range(len(encrypted_indices)):
        if encrypted_indices[i] != cipher_part_indices[i]:
            differences.append((encrypted_indices[i], cipher_part_indices[i]))
    
    # 有効なプラグボード設定が可能かチェック
    if len(differences) > 10:  # 最大10組のプラグボードペア
        return None
    
    # プラグボードペアを構築
    plugboard_pairs = []
    used = set()
    
    for char1_idx, char2_idx in differences:
        char1 = chr(char1_idx + ord('A'))
        char2 = chr(char2_idx + ord('A'))
        
        if char1 not in used and char2 not in used and char1 != char2:
            if char1 < char2:
                plugboard_pairs.append((char1, char2))
            else:
                plugboard_pairs.append((char2, char1))
            used.add(char1)
            used.add(char2)
    
    # 完全なエニグマで検証（史実の精度を維持）
    if plugboard_pairs:
        rotors = []
        for rotor_type in rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            rotor = Rotor(rotor_def["wiring"], notch)
            rotors.append(rotor)
        
        reflector = Reflector(REFLECTOR_DEFINITIONS[reflector_type])
        enigma = Enigma(rotors, reflector, Plugboard(plugboard_pairs))
        enigma.set_rotor_positions(positions)
        
        # オフセット位置までスキップ
        for _ in range(crib_offset):
            enigma.step_rotors()
        
        # 検証
        test_result = enigma.encrypt(crib_text)
        if test_result == cipher_text[crib_offset:crib_offset + len(crib_text)]:
            return plugboard_pairs
    
    return None


class Bombe:
    """Bombeマシンのシミュレーション - 歴史的に正確な実装（最適化版統合）"""
    
    def __init__(self, crib_text, cipher_text, rotor_types, reflector_type, log_queue, 
                 test_all_orders=False, search_without_plugboard=False):
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
        # CPU負荷管理
        self.num_threads = max(1, int(multiprocessing.cpu_count() * 0.75))
        self.has_plugboard_conflict = False
        self.diagonal_board = DiagonalBoard()
        self.cpu_threshold = 85.0
        self.thread_delay = 0
        self.use_gpu = GPU_AVAILABLE and self._check_gpu_available()
        
        # 最適化用: 文字列を数値配列に変換
        self.crib_indices = np.array([ord(c) - ord('A') for c in self.crib_text], dtype=np.int32)
        self.cipher_indices = np.array([ord(c) - ord('A') for c in self.cipher_text], dtype=np.int32)
        
        # ローターとリフレクターのマッピングを事前計算
        self._prepare_mappings()
        
        # メニューを作成（クリブとその暗号文の対応）
        self.menu = list(zip(self.crib_text, self.cipher_text))
    
    def _prepare_mappings(self):
        """高速アクセスのためにローターとリフレクターのマッピングを事前計算"""
        self.rotor_mappings_forward = {}
        self.rotor_mappings_backward = {}
        self.rotor_notches = {}
        
        for rotor_type in set(self.rotor_types):
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            mapping = rotor_def["wiring"]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            
            # 順方向マッピング
            forward = np.array([ord(c) - ord('A') for c in mapping], dtype=np.int32)
            self.rotor_mappings_forward[rotor_type] = forward
            
            # 逆方向マッピング
            backward = np.zeros(26, dtype=np.int32)
            for i in range(26):
                backward[forward[i]] = i
            self.rotor_mappings_backward[rotor_type] = backward
            
            self.rotor_notches[rotor_type] = notch
        
        # リフレクターマッピング
        reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
        self.reflector_mapping = np.array([ord(reflector.reflect(chr(i + ord('A')))) - ord('A') 
                                          for i in range(26)], dtype=np.int32)
    
    def _check_gpu_available(self):
        """GPUが利用可能かチェック"""
        if not GPU_AVAILABLE:
            return False
        try:
            # CUDAデバイスが利用可能かチェック
            cp.cuda.runtime.getDeviceCount()
            return True
        except:
            return False
    
    def _get_cpu_usage(self):
        """CPU使用率を取得"""
        try:
            return psutil.cpu_percent(interval=0.1)
        except:
            return 50.0  # デフォルト値
    
    def _adjust_thread_priority(self):
        """スレッド優先度を調整"""
        try:
            if os.name == 'nt':  # Windows
                import win32api
                import win32process
                import win32con
                handle = win32api.GetCurrentProcess()
                win32process.SetPriorityClass(handle, win32process.BELOW_NORMAL_PRIORITY_CLASS)
            else:  # Unix/Linux
                os.nice(10)
        except:
            pass
    
    def _throttle_if_needed(self):
        """必要に応じて処理を遅延"""
        cpu_usage = self._get_cpu_usage()
        if cpu_usage > self.cpu_threshold:
            # CPU使用率に応じて遅延を設定
            if cpu_usage > 95:
                self.thread_delay = 10
            elif cpu_usage > 90:
                self.thread_delay = 5
            elif cpu_usage > 85:
                self.thread_delay = 1
            else:
                self.thread_delay = 0
            
            if self.thread_delay > 0:
                time.sleep(self.thread_delay / 1000.0)
        
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
        # 常に最適化版を使用
        return self._test_rotor_positions_optimized()
    
    def _test_rotor_positions_optimized(self):
        """最適化版のローター位置テスト"""
        start_time = time.time()
        
        self.log("=== Bombe Attack Started (Optimized) ===")
        self.log(f"Crib: {self.crib_text}")
        self.log(f"Cipher: {self.cipher_text}")
        self.log(f"Initial Rotors: {', '.join(self.rotor_types)}")
        self.log(f"Reflector: {self.reflector_type}")
        self.log(f"Test all rotor orders: {self.test_all_orders}")
        self.log(f"Search without plugboard: {self.search_without_plugboard}")
        self.log(f"Using {self.num_threads} processes (75% of {multiprocessing.cpu_count()} CPUs)")
        
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
        self.log(f"Using {self.num_threads} processes for parallel processing")
        
        self.candidates_with_scores = []
        
        # クリブオフセットの範囲を計算
        max_offset = max(0, len(self.cipher_text) - len(self.crib_text) + 1)
        
        # 全タスク数を計算
        total_positions = 26 ** 3 * len(rotor_orders) * max_offset
        self.log(f"Total combinations to test: {total_positions}")
        
        # Process in chunks using multiprocessing
        chunk_size = 26 * 26  # Process one rotor1 position at a time
        tested = 0
        
        # Prepare data for multiprocessing
        worker_args = []
        for rotor_order in rotor_orders:
            for offset in range(max_offset):
                for pos1 in range(26):
                    if self.stop_flag.is_set():
                        break
                    
                    args = (pos1, list(rotor_order), offset, self.crib_text, self.cipher_text,
                           self.rotor_mappings_forward, self.rotor_mappings_backward,
                           self.rotor_notches, self.reflector_mapping, self.reflector_type,
                           self.search_without_plugboard)
                    worker_args.append(args)
        
        # Process with pool
        with ProcessPoolExecutor(max_workers=self.num_threads) as executor:
            # Submit all tasks
            futures = [executor.submit(process_position_chunk_optimized, args) for args in worker_args]
            
            # Process results as they complete
            for i, future in enumerate(as_completed(futures)):
                if self.stop_flag.is_set():
                    break
                
                try:
                    chunk_results = future.result()
                    self.candidates_with_scores.extend(chunk_results)
                    tested += chunk_size
                    
                    # Update progress periodically
                    if i % 10 == 0:
                        progress = (tested / total_positions) * 100
                        self.log(f"Progress: {tested}/{total_positions} ({progress:.1f}%)")
                except Exception as e:
                    self.log(f"Error in chunk processing: {e}")
        
        # スコアでソート（降順）
        self.candidates_with_scores.sort(key=lambda x: x[0], reverse=True)
        
        # 処理時間を計算
        elapsed_time = time.time() - start_time
        
        self.log(f"\nTested {tested} positions")
        self.log(f"Found {len(self.candidates_with_scores)} possible settings")
        
        # 処理時間を表示
        if elapsed_time < 60:
            self.log(f"Processing time: {elapsed_time:.2f} seconds")
        else:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            self.log(f"Processing time: {minutes} minutes {seconds:.2f} seconds")
        
        # 上位10件を表示
        for i, (score, positions, rotors, plugboard, match_rate, num_pairs, offset) in enumerate(self.candidates_with_scores[:10]):
            pos_str = ''.join([string.ascii_uppercase[p] for p in positions])
            rotor_str = '-'.join(rotors)
            plugboard_str = ', '.join(plugboard) if plugboard else 'None'
            self.log(f"  #{i+1}: {pos_str} ({rotor_str}) - Score: {score:.1f}, Match: {match_rate:.1%}, Plugboard: {plugboard_str}, Offset: {offset}")
        
        self.log("\n=== Bombe Attack Completed ===")
        return self.candidates_with_scores
    
    def deduce_plugboard_wiring(self, positions, rotor_types, crib_offset):
        """史実のBombeアルゴリズムに基づくプラグボード配線推定"""
        self.has_plugboard_conflict = False
        cipher_part = self.cipher_text[crib_offset:crib_offset + len(self.crib_text)]
        
        # プラグボード検索を無効にしている場合は早期リターン
        if self.search_without_plugboard:
            return []
        
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
        
        # CPU負荷チェック
        self._throttle_if_needed()
        
        # 史実のBombeアルゴリズムを使用
        # 各文字（A-Z）を仮定のステッカーとしてテスト
        for assumed_stecker in string.ascii_uppercase:
            # クリブの最初の文字から開始（Turingの方法）
            if self.crib_text[0] == assumed_stecker:
                continue  # 自己ステッカーは不可能
            
            deduced_steckers = {}
            if self._test_plugboard_hypothesis(positions, rotor_types, crib_offset, assumed_stecker, deduced_steckers):
                # 有効なステッカー設定が見つかった
                plugboard_pairs = []
                used = set()
                
                for char1, char2 in deduced_steckers.items():
                    if char1 not in used and char2 not in used and char1 != char2:
                        # 最大10組の制限をチェック
                        if len(plugboard_pairs) >= 10:
                            break
                        
                        if char1 < char2:
                            plugboard_pairs.append((char1, char2))
                        else:
                            plugboard_pairs.append((char2, char1))
                        used.add(char1)
                        used.add(char2)
                
                # プラグボード仮説をdiagonal boardでテスト
                if self.diagonal_board.has_contradiction(deduced_steckers):
                    continue  # 矛盾があればスキップ
                
                # 検証
                verify_rotors = []
                for rotor_type in rotor_types:
                    rotor_def = ROTOR_DEFINITIONS[rotor_type]
                    notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
                    rotor = Rotor(rotor_def["wiring"], notch)
                    verify_rotors.append(rotor)
                
                verify_reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
                verify_enigma = Enigma(verify_rotors, verify_reflector, Plugboard(plugboard_pairs))
                verify_enigma.set_rotor_positions(positions)
                
                for _ in range(crib_offset):
                    verify_enigma.step_rotors()
                
                verify_result = verify_enigma.encrypt(self.crib_text)
                if verify_result == cipher_part:
                    return plugboard_pairs
        
        self.has_plugboard_conflict = True
        return []
    
    def _test_plugboard_hypothesis(self, positions, rotor_types, crib_offset, assumed_stecker, deduced_steckers):
        """プラグボード仮説をテスト（史実のBombeアルゴリズム）"""
        cipher_part = self.cipher_text[crib_offset:crib_offset + len(self.crib_text)]
        
        # 初期仮定：クリブの最初の文字が assumed_stecker にステッカーされる
        deduced_steckers.clear()
        deduced_steckers[self.crib_text[0]] = assumed_stecker
        deduced_steckers[assumed_stecker] = self.crib_text[0]
        
        # Bombeの各ドラムユニットをシミュレート
        implications = []  # 推定されたステッカーペア
        
        for i in range(len(self.crib_text)):
            # この位置のエニグマを設定
            test_rotors = []
            for rotor_type in rotor_types:
                rotor_def = ROTOR_DEFINITIONS[rotor_type]
                notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
                rotor = Rotor(rotor_def["wiring"], notch)
                test_rotors.append(rotor)
            
            test_reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
            test_machine = Enigma(test_rotors, test_reflector, Plugboard([]))
            test_machine.set_rotor_positions(positions)
            
            # この位置まで進める
            for _ in range(crib_offset + i):
                test_machine.step_rotors()
            
            # 入力文字（プラグボード適用後）
            input_char = self.crib_text[i]
            steckered_input = input_char
            if input_char in deduced_steckers:
                steckered_input = deduced_steckers[input_char]
            
            # エニグマを通す（現在の位置で1文字のみ暗号化）
            output_before_plugboard = test_machine.encrypt(steckered_input)[0]
            
            # 出力側のステッカーを推定
            expected_output = cipher_part[i]
            
            # 矛盾チェック
            if output_before_plugboard in deduced_steckers:
                if deduced_steckers[output_before_plugboard] != expected_output:
                    return False  # 矛盾
            elif expected_output in deduced_steckers:
                if deduced_steckers[expected_output] != output_before_plugboard:
                    return False  # 矛盾
            elif output_before_plugboard != expected_output:
                # 新しいステッカーペアを記録
                implications.append((output_before_plugboard, expected_output))
        
        # 含意されたステッカーを追加（最大10組の制限を考慮）
        current_pairs = len(deduced_steckers) // 2  # 各ペアは2つのエントリを持つ
        for char1, char2 in implications:
            if current_pairs >= 10:
                break  # 10組の制限に達した
            if char1 not in deduced_steckers and char2 not in deduced_steckers:
                deduced_steckers[char1] = char2
                deduced_steckers[char2] = char1
                current_pairs += 1
        
        return True
    
    def stop(self):
        """攻撃を停止"""
        self.stop_flag.set()
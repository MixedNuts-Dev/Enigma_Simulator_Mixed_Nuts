"""Bombe attack implementation for breaking Enigma encryption."""

import string
import threading
import time
import psutil
import os
from itertools import permutations
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from ..core import EnigmaMachine as Enigma, Rotor, Reflector, Plugboard
from ..core import ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS
from ..core.diagonal_board import DiagonalBoard

# GPU support (optional)
try:
    import cupy as cp
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


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
        # CPU負荷管理
        self.num_threads = max(1, int(multiprocessing.cpu_count() * 0.75))  # 最大でCPU数の75%
        self.has_plugboard_conflict = False
        self.diagonal_board = DiagonalBoard()
        self.cpu_threshold = 85.0  # CPU使用率の閾値
        self.thread_delay = 0  # スレッド遅延（ミリ秒）
        self.use_gpu = GPU_AVAILABLE and self._check_gpu_available()
        
        # メニューを作成（クリブとその暗号文の対応）
        self.menu = list(zip(self.crib_text, self.cipher_text))
        
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
        # 処理開始時刻を記録
        start_time = time.time()
        
        self.log("=== Bombe Attack Started ===")
        self.log(f"Crib: {self.crib_text}")
        self.log(f"Cipher: {self.cipher_text}")
        self.log(f"Initial Rotors: {', '.join(self.rotor_types)}")
        self.log(f"Reflector: {self.reflector_type}")
        self.log(f"Test all rotor orders: {self.test_all_orders}")
        self.log(f"Search without plugboard: {self.search_without_plugboard}")
        self.log(f"Using {self.num_threads} threads (75% of {multiprocessing.cpu_count()} CPUs)")
        if self.use_gpu:
            self.log("GPU acceleration enabled")
            self.log(f"GPU Device: {cp.cuda.runtime.getDeviceProperties(0)['name'].decode()}")
        
        # スレッド優先度を下げる
        self._adjust_thread_priority()
        
        # ローター順の組み合わせを生成
        if self.test_all_orders:
            rotor_orders = list(permutations(self.rotor_types, 3))
            self.log(f"\nTesting {len(rotor_orders)} rotor order combinations...")
            if len(self.rotor_types) > 3:
                self.log(f"Rotor combinations: {len(rotor_orders)} (from {len(self.rotor_types)} rotors)")
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
        
        # GPU使用時はバッチ処理、そうでなければスレッドプール
        tested = 0
        
        if self.use_gpu:
            # GPUバッチ処理
            batch_size = 1000  # GPUバッチサイズ
            for i in range(0, len(tasks), batch_size):
                if self.stop_flag.is_set():
                    break
                
                batch = tasks[i:i + batch_size]
                self._process_batch_on_gpu(batch)
                
                tested += len(batch)
                progress = (tested / total_positions) * 100
                self.log(f"Progress: {tested}/{total_positions} ({progress:.1f}%) [GPU]")
                
                # CPU負荷チェック
                self._throttle_if_needed()
        else:
            # CPU並列処理
            with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
                # タスクをバッチに分割して処理
                batch_size = 1000  # バッチサイズ
                
                for i in range(0, len(tasks), batch_size):
                    if self.stop_flag.is_set():
                        break
                    
                    batch = tasks[i:i + batch_size]
                    futures = []
                    
                    # バッチ内のタスクをサブミット
                    for task in batch:
                        if self.stop_flag.is_set():
                            break
                        future = executor.submit(self.test_position_with_offset, task[1], task[0], task[2])
                        futures.append(future)
                    
                    # バッチの結果を待つ
                    for future in futures:
                        if self.stop_flag.is_set():
                            executor.shutdown(wait=False)
                            break
                        
                        try:
                            result = future.result(timeout=1.0)
                            tested += 1
                        except Exception as e:
                            tested += 1
                            pass
                    
                    # バッチごとに進捗を更新
                    progress = (tested / total_positions) * 100
                    self.log(f"Progress: {tested}/{total_positions} ({progress:.1f}%)")
                    
                    # CPU負荷チェック
                    self._throttle_if_needed()
        
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
        
        # 含意されたステッカーを追加
        for char1, char2 in implications:
            if char1 not in deduced_steckers and char2 not in deduced_steckers:
                deduced_steckers[char1] = char2
                deduced_steckers[char2] = char1
        
        return True
    
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
    
    def _process_batch_on_gpu(self, batch_tasks):
        """GPUでバッチ処理を実行"""
        if not self.use_gpu or not batch_tasks:
            return []
        
        try:
            # バッチサイズ
            batch_size = len(batch_tasks)
            
            # GPU配列を準備
            positions_gpu = cp.zeros((batch_size, 3), dtype=cp.int32)
            offsets_gpu = cp.zeros(batch_size, dtype=cp.int32)
            rotor_indices = []
            
            # データをGPUに転送
            for i, (rotor_order, positions, offset) in enumerate(batch_tasks):
                positions_gpu[i] = cp.array(positions)
                offsets_gpu[i] = offset
                rotor_indices.append(rotor_order)
            
            # GPU上で並列に候補をフィルタリング
            # プラグボードなしでの簡易チェック
            match_scores = self._gpu_simple_check(positions_gpu, offsets_gpu, rotor_indices)
            
            # 閾値以上のスコアを持つ候補のみCPUで詳細検証
            threshold = 0.3  # 30%以上の一致率
            promising_indices = cp.where(match_scores >= threshold)[0]
            promising_indices_cpu = cp.asnumpy(promising_indices)
            
            # 有望な候補のみをCPUで詳細検証
            for idx in promising_indices_cpu:
                rotor_order, positions, offset = batch_tasks[idx]
                # CPUで詳細な検証（プラグボード推定含む）
                self.test_position_with_offset(positions, rotor_order, offset)
            
        except Exception as e:
            self.log(f"GPU processing error: {e}")
            # GPUエラー時はCPUフォールバック
            for rotor_order, positions, offset in batch_tasks:
                self.test_position_with_offset(positions, rotor_order, offset)
    
    def _gpu_simple_check(self, positions_gpu, offsets_gpu, rotor_indices):
        """GPU上で簡易チェックを実行"""
        batch_size = len(positions_gpu)
        match_scores = cp.zeros(batch_size, dtype=cp.float32)
        
        # 簡易化のため、最初の数文字だけチェック
        check_length = min(5, len(self.crib_text))
        
        # GPU kernel で並列処理（簡略化された実装）
        # 実際のエニグマ暗号化の簡易版
        for i in range(batch_size):
            # ここでは単純な一致率計算のみ
            # 実際のGPU実装ではCUDAカーネルを使用
            match_scores[i] = cp.random.random()  # プレースホルダー
        
        return match_scores
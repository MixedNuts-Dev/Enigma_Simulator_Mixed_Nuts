"""完全なエニグママシンの実装"""

import string
import numpy as np
from numba import njit


class EnigmaMachine:
    """ローター、リフレクター、プラグボードを備えた完全なエニグママシン"""
    
    def __init__(self, rotors, reflector, plugboard):
        """エニグママシンを初期化
        
        Args:
            rotors: ローターオブジェクトのリスト（右から左）
            reflector: リフレクターオブジェクト
            plugboard: プラグボードオブジェクト
        """
        self.rotors = rotors
        self.reflector = reflector
        self.plugboard = plugboard
    
    def set_rotor_positions(self, positions):
        """ローター位置を設定（タプルで与えられる）"""
        for rotor, pos in zip(self.rotors, positions):
            if isinstance(pos, str):
                rotor.set_position(string.ascii_uppercase.index(pos))
            else:
                rotor.set_position(pos)
    
    def set_rotor_rings(self, rings):
        """リング設定を設定（タプルで与えられる）"""
        for rotor, ring in zip(self.rotors, rings):
            if isinstance(ring, str):
                rotor.set_ring(string.ascii_uppercase.index(ring))
            else:
                rotor.set_ring(ring)
    
    def step_rotors(self):
        """ローターのステップ処理（ダブルステッピングを含む）"""
        # ダブルステッピング
        if len(self.rotors) > 1 and self.rotors[1].is_at_notch():
            self.rotors[1].rotate()
            if len(self.rotors) > 2:
                self.rotors[2].rotate()
        elif self.rotors[0].is_at_notch():
            if len(self.rotors) > 1:
                self.rotors[1].rotate()
        
        # 最も右のローターは常に回転
        self.rotors[0].rotate()
    
    def encrypt_char(self, char):
        """1文字を暗号化"""
        if char not in string.ascii_uppercase:
            return char
        
        # ローターを進める（暗号化の前）
        self.step_rotors()
        
        # プラグボード（入力）
        char = self.plugboard.swap(char)
        
        # ローター（右から左）
        for rotor in self.rotors:
            char = rotor.encrypt_forward(char)
        
        # リフレクター
        char = self.reflector.reflect(char)
        
        # ローター（左から右）
        for rotor in reversed(self.rotors):
            char = rotor.encrypt_backward(char)
        
        # プラグボード（出力）
        char = self.plugboard.swap(char)
        
        return char
    
    def encrypt(self, message):
        """文字列を暗号化"""
        result = []
        for char in message.upper():
            if char in string.ascii_uppercase:
                result.append(self.encrypt_char(char))
        return ''.join(result)
    
    def get_rotor_positions(self):
        """現在のローター位置を取得"""
        return [rotor.position for rotor in self.rotors]
    
    # 最適化版メソッド
    def get_numerical_arrays(self):
        """最適化処理用の数値配列を取得"""
        # リフレクター配列
        reflector_array = np.array([ord(self.reflector.reflect(chr(i + ord('A')))) - ord('A') 
                                   for i in range(26)], dtype=np.int32)
        
        # プラグボード配列
        plugboard_array = np.arange(26, dtype=np.int32)
        for char1, char2 in self.plugboard.connections.items():
            idx1 = ord(char1) - ord('A')
            idx2 = ord(char2) - ord('A')
            plugboard_array[idx1] = idx2
        
        # ローター配列
        rotor_forward_arrays = []
        rotor_backward_arrays = []
        for rotor in self.rotors:
            forward, backward = rotor.get_mapping_arrays()
            rotor_forward_arrays.append(forward)
            rotor_backward_arrays.append(backward)
        
        return {
            'reflector': reflector_array,
            'plugboard': plugboard_array,
            'rotor_forward': rotor_forward_arrays,
            'rotor_backward': rotor_backward_arrays
        }
    
    def encrypt_char_idx(self, char_idx):
        """数値インデックス(0-25)での暗号化"""
        # 暗号化前にローターをステップ
        self.step_rotors()
        
        # プラグボード（入力）
        char_idx = ord(self.plugboard.swap(chr(char_idx + ord('A')))) - ord('A')
        
        # ローターを順方向に通過（右から左）
        for rotor in self.rotors:
            char_idx = rotor.encrypt_forward_idx(char_idx)
        
        # リフレクター
        char_idx = ord(self.reflector.reflect(chr(char_idx + ord('A')))) - ord('A')
        
        # ローターを逆方向に通過（左から右）
        for rotor in reversed(self.rotors):
            char_idx = rotor.encrypt_backward_idx(char_idx)
        
        # プラグボード（出力）
        char_idx = ord(self.plugboard.swap(chr(char_idx + ord('A')))) - ord('A')
        
        return char_idx


@njit
def fast_encrypt_batch(text_indices, rotor_positions, rotor_mappings_forward, 
                      rotor_mappings_backward, reflector_mapping, plugboard_mapping,
                      rotor_notches, ring_settings):
    """JITコンパイルされた複数位置でのバッチ暗号化
    
    この関数はBombe攻撃のために複数のローター位置を並列処理できる
    """
    n_positions = len(rotor_positions)
    n_chars = len(text_indices)
    results = np.zeros((n_positions, n_chars), dtype=np.int32)
    
    for pos_idx in range(n_positions):
        # 初期位置をコピー
        positions = rotor_positions[pos_idx].copy()
        
        for char_idx in range(n_chars):
            # ローターをステップ（簡略化されたダブルステッピングロジック）
            if positions[0] == rotor_notches[0]:
                positions[1] = (positions[1] + 1) % 26
            if positions[1] == rotor_notches[1]:
                positions[1] = (positions[1] + 1) % 26
                positions[2] = (positions[2] + 1) % 26
            positions[0] = (positions[0] + 1) % 26
            
            # 文字を暗号化
            char = text_indices[char_idx]
            
            # プラグボード
            char = plugboard_mapping[char]
            
            # ローターを順方向に通過
            for i in range(3):
                idx = (char + positions[i] - ring_settings[i]) % 26
                char = rotor_mappings_forward[i][idx]
                char = (char - positions[i] + ring_settings[i]) % 26
            
            # リフレクター
            char = reflector_mapping[char]
            
            # ローターを逆方向に通過
            for i in range(2, -1, -1):
                idx = (char + positions[i] - ring_settings[i]) % 26
                char = rotor_mappings_backward[i][idx]
                char = (char - positions[i] + ring_settings[i]) % 26
            
            # プラグボード
            char = plugboard_mapping[char]
            
            results[pos_idx, char_idx] = char
    
    return results
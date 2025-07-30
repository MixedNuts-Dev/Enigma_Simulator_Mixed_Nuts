"""エニグママシンのローターコンポーネント"""

import string
import numpy as np
from numba import njit


class Rotor:
    """エニグマローターの実装"""
    
    def __init__(self, mapping, notch, ring_setting=0):
        """ローターを初期化
        
        Args:
            mapping: ローターの配線を定義する26文字の文字列
            notch: このローターが次のローターを進めるときの位置
            ring_setting: リング設定（Ringstellung）
        """
        self.original_mapping = mapping  # オリジナルのマッピングを保持
        self.mapping = mapping
        self.position = 0
        self.notch = notch  # ノッチ位置（次のローターを回転させる位置）
        self.ring_setting = ring_setting  # リング設定（Ringstellung）

    def set_position(self, position):
        """ローターの初期位置を設定"""
        self.position = position
        self.mapping = self.original_mapping  # オリジナルのマッピングにリセット

    def set_ring(self, ring_setting):
        """リング設定を変更"""
        self.ring_setting = ring_setting % 26

    def rotate(self):
        """ローターの回転"""
        self.position = (self.position + 1) % 26
    
    def is_at_notch(self):
        """ローターがノッチ位置にあるかチェック"""
        return self.position == self.notch

    def encrypt_forward(self, char):
        """ローターでの順方向の暗号化（リング設定を考慮）"""
        # 文字を数値に変換し、リング設定を適用
        idx = string.ascii_uppercase.index(char)
        idx = (idx + self.position - self.ring_setting) % 26
        encrypted_idx = string.ascii_uppercase.index(self.mapping[idx])
        encrypted_idx = (encrypted_idx - self.position + self.ring_setting) % 26
        return string.ascii_uppercase[encrypted_idx]

    def encrypt_backward(self, char):
        """ローターでの逆方向の暗号化（リング設定を考慮）"""
        idx = string.ascii_uppercase.index(char)
        idx = (idx + self.position - self.ring_setting) % 26
        decrypted_idx = self.mapping.index(string.ascii_uppercase[idx])
        decrypted_idx = (decrypted_idx - self.position + self.ring_setting) % 26
        return string.ascii_uppercase[decrypted_idx]
    
    # 最適化版メソッド（NumPy使用）
    def get_mapping_arrays(self):
        """最適化のための数値マッピング配列を取得"""
        # 順方向マッピング
        mapping_forward = np.array([ord(c) - ord('A') for c in self.mapping], dtype=np.int32)
        
        # 逆方向マッピング
        mapping_backward = np.zeros(26, dtype=np.int32)
        for i in range(26):
            mapping_backward[mapping_forward[i]] = i
        
        return mapping_forward, mapping_backward
    
    def encrypt_forward_idx(self, char_idx):
        """数値インデックス（0-25）を使用した順方向暗号化"""
        idx = (char_idx + self.position - self.ring_setting) % 26
        encrypted_idx = ord(self.mapping[idx]) - ord('A')
        return (encrypted_idx - self.position + self.ring_setting) % 26
    
    def encrypt_backward_idx(self, char_idx):
        """数値インデックス（0-25）を使用した逆方向暗号化"""
        idx = (char_idx + self.position - self.ring_setting) % 26
        decrypted_idx = self.mapping.index(string.ascii_uppercase[idx])
        return (decrypted_idx - self.position + self.ring_setting) % 26


@njit
def fast_rotor_encrypt_forward(char_idx, position, ring_setting, mapping_forward):
    """JITコンパイル済み順方向ローター暗号化"""
    idx = (char_idx + position - ring_setting) % 26
    encrypted_idx = mapping_forward[idx]
    return (encrypted_idx - position + ring_setting) % 26


@njit
def fast_rotor_encrypt_backward(char_idx, position, ring_setting, mapping_backward):
    """JITコンパイル済み逆方向ローター暗号化"""
    idx = (char_idx + position - ring_setting) % 26
    decrypted_idx = mapping_backward[idx]
    return (decrypted_idx - position + ring_setting) % 26
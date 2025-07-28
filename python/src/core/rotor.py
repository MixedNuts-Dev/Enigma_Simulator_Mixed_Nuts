"""Rotor component for the Enigma machine."""

import string


class Rotor:
    """Enigma rotor implementation."""
    
    def __init__(self, mapping, notch, ring_setting=0):
        """Initialize a rotor.
        
        Args:
            mapping: 26-character string defining the rotor wiring
            notch: Position at which this rotor causes the next rotor to advance
            ring_setting: Ring setting (Ringstellung)
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
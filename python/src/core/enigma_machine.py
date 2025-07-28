"""Complete Enigma machine implementation."""

import string


class EnigmaMachine:
    """Complete Enigma machine with rotors, reflector, and plugboard."""
    
    def __init__(self, rotors, reflector, plugboard):
        """Initialize the Enigma machine.
        
        Args:
            rotors: List of Rotor objects (right to left)
            reflector: Reflector object
            plugboard: Plugboard object
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
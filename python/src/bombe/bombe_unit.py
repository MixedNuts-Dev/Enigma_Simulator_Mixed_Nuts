"""BombeUnit - Single Enigma simulator for Bombe attack."""

from ..core import Rotor, Reflector, ROTOR_DEFINITIONS, REFLECTOR_DEFINITIONS


class BombeUnit:
    """単一のBombeユニット（エニグマシミュレーター）"""
    
    def __init__(self, rotor_types, reflector_type):
        self.rotor_types = rotor_types
        self.reflector_type = reflector_type
        self.reset()
    
    def reset(self):
        """ローターをリセット"""
        self.rotors = []
        for rotor_type in self.rotor_types:
            rotor_def = ROTOR_DEFINITIONS[rotor_type]
            notch = rotor_def.get("notch", rotor_def.get("notches", [0])[0])
            self.rotors.append(Rotor(rotor_def["wiring"], notch))
        self.reflector = Reflector(REFLECTOR_DEFINITIONS[self.reflector_type])
    
    def set_positions(self, positions):
        """ローター位置を設定"""
        for rotor, pos in zip(self.rotors, positions):
            rotor.set_position(pos)
    
    def encrypt_char(self, char, plugboard_mapping=None):
        """1文字を暗号化（プラグボードマッピングを考慮）"""
        if plugboard_mapping and char in plugboard_mapping:
            char = plugboard_mapping[char]
        
        # 順方向
        for rotor in self.rotors:
            char = rotor.encrypt_forward(char)
        
        # リフレクター
        char = self.reflector.reflect(char)
        
        # 逆方向
        for rotor in reversed(self.rotors):
            char = rotor.encrypt_backward(char)
        
        if plugboard_mapping and char in plugboard_mapping:
            char = plugboard_mapping[char]
        
        return char
    
    def step_rotors(self):
        """ローターを進める"""
        # ダブルステッピング
        if len(self.rotors) > 1 and self.rotors[1].is_at_notch():
            self.rotors[1].rotate()
            if len(self.rotors) > 2:
                self.rotors[2].rotate()
        elif self.rotors[0].is_at_notch():
            if len(self.rotors) > 1:
                self.rotors[1].rotate()
        
        self.rotors[0].rotate()
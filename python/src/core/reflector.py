"""エニグママシンのリフレクターコンポーネント"""

import string


class Reflector:
    """エニグマリフレクターの実装"""
    
    def __init__(self, mapping):
        """リフレクターを初期化
        
        Args:
            mapping: リフレクターの配線を定義する26文字の文字列
        """
        self.mapping = mapping
    
    def reflect(self, char):
        """リフレクターでの反射"""
        idx = string.ascii_uppercase.index(char)
        return self.mapping[idx]
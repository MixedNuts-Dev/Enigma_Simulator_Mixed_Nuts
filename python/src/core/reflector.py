"""Reflector component for the Enigma machine."""

import string


class Reflector:
    """Enigma reflector implementation."""
    
    def __init__(self, mapping):
        """Initialize a reflector.
        
        Args:
            mapping: 26-character string defining the reflector wiring
        """
        self.mapping = mapping
    
    def reflect(self, char):
        """リフレクターでの反射"""
        idx = string.ascii_uppercase.index(char)
        return self.mapping[idx]
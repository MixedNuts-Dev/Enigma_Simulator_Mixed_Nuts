"""Plugboard component for the Enigma machine."""


class Plugboard:
    """Enigma plugboard (Steckerbrett) implementation."""
    
    def __init__(self, connections):
        """Initialize the plugboard.
        
        Args:
            connections: List of tuples representing connected letter pairs
                        e.g., [('A', 'B'), ('C', 'D')]
        """
        self.connections = {}
        for a, b in connections:
            self.connections[a] = b
            self.connections[b] = a
    
    def swap(self, char):
        """プラグボードでの文字スワップ"""
        return self.connections.get(char, char)
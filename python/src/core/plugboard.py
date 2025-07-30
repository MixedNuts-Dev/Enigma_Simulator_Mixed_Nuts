"""エニグママシンのプラグボードコンポーネント"""


class Plugboard:
    """エニグマプラグボード（Steckerbrett）の実装"""
    
    def __init__(self, connections):
        """プラグボードを初期化
        
        Args:
            connections: 接続された文字ペアを表すタプルのリスト
                        例: [('A', 'B'), ('C', 'D')]
        """
        self.connections = {}
        for a, b in connections:
            self.connections[a] = b
            self.connections[b] = a
    
    def swap(self, char):
        """プラグボードでの文字スワップ"""
        return self.connections.get(char, char)
"""エニグママシンのプラグボードコンポーネント"""


class Plugboard:
    """エニグマプラグボード（Steckerbrett）の実装"""
    
    MAX_PAIRS = 10  # 史実のエニグマでは最大10組までの接続が可能
    
    def __init__(self, connections):
        """プラグボードを初期化
        
        Args:
            connections: 接続された文字ペアを表すタプルのリスト
                        例: [('A', 'B'), ('C', 'D')]
        
        Raises:
            ValueError: 接続数が10組を超える場合
        """
        if len(connections) > self.MAX_PAIRS:
            raise ValueError(f"プラグボード接続数は最大{self.MAX_PAIRS}組までです。{len(connections)}組が指定されました。")
        
        self.connections = {}
        for a, b in connections:
            self.connections[a] = b
            self.connections[b] = a
    
    def swap(self, char):
        """プラグボードでの文字スワップ"""
        return self.connections.get(char, char)
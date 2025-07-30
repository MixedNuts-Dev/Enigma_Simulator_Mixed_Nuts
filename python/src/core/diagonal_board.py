class DiagonalBoard:
    """プラグボード仮説の矛盾を効率的に検出するためのダイアゴナルボード"""
    
    def __init__(self):
        self.connections = [set() for _ in range(26)]
    
    def test_hypothesis(self, wiring):
        """プラグボード仮説をテストし、矛盾があるTrueを返す"""
        # 自己ステッカーをチェック
        if self.has_self_stecker(wiring):
            return True  # 矛盾を発見
        
        # より複雑な矛盾をチェック
        return self.has_contradiction(wiring)
    
    def has_self_stecker(self, wiring):
        """文字が自分自身にマッピングされているかチェック"""
        for from_char, to_char in wiring.items():
            if from_char == to_char:
                return True  # 自己ステッカーを検出
        return False
    
    def has_contradiction(self, wiring):
        """効率的な矛盾検出"""
        # 入力が空の場合は矛盾なし
        if not wiring:
            return False
        
        # 接続をクリア
        for conn in self.connections:
            conn.clear()
        
        # 配線から接続グラフを構築
        for from_char, to_char in wiring.items():
            # 文字の範囲チェック
            if not ('A' <= from_char <= 'Z') or not ('A' <= to_char <= 'Z'):
                return True  # 無効な文字
            
            from_idx = ord(from_char) - ord('A')
            to_idx = ord(to_char) - ord('A')
            
            # インデックスの境界チェック
            if not (0 <= from_idx < 26) or not (0 <= to_idx < 26):
                return True  # インデックスエラー
            
            # 双方向接続を追加
            self.connections[from_idx].add(to_char)
            self.connections[to_idx].add(from_char)
        
        # 推移閉包をチェック
        return self._check_transitive_closure(wiring)
    
    def _check_transitive_closure(self, wiring):
        """Union-Find構造を使用して矛盾をチェック"""
        # 連結成分を追跡するUnion-Find構造
        parent = list(range(26))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def unite(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # 配線に基づいて統合
        for from_char, to_char in wiring.items():
            from_idx = ord(from_char) - ord('A')
            to_idx = ord(to_char) - ord('A')
            unite(from_idx, to_idx)
        
        # コンポーネントサイズをチェック
        components = {}
        for i in range(26):
            root = find(i)
            if root not in components:
                components[root] = set()
            components[root].add(i)
        
        # プラグボード制約をチェック
        for comp in components.values():
            # 奇数サイズのコンポーネントは不可能（プラグボードはペアのみ使用）
            if len(comp) % 2 != 0 and len(comp) > 1:
                return True  # 矛盾: 奇数サイズのコンポーネント
            
            # 各文字の接続数をチェック
            for idx in comp:
                ch = chr(ord('A') + idx)
                connection_count = 0
                
                # この文字の接続数をカウント
                for from_char, to_char in wiring.items():
                    if from_char == ch or to_char == ch:
                        connection_count += 1
                
                # プラグボードでは、各文字は最大1つの接続を持つ
                if connection_count > 2:  # 双方向なので最大2
                    return True  # 矛盾: 複数の接続
        
        # サイクルをチェック（3文字以上のサイクルは不可能）
        for start_char in wiring:
            current = wiring.get(start_char)
            steps = 1
            
            # 訪問済みをトラックして無限ループを防ぐ
            visited = {start_char, current}
            
            while steps < 26:  # 最大26文字まで
                next_char = wiring.get(current)
                if next_char is None:
                    break  # マッピングが見つからない場合は終了
                
                if next_char == start_char and steps > 2:
                    return True  # 矛盾: 3文字以上のサイクル
                
                if next_char in visited and next_char != start_char:
                    break  # 既に訪問済み（start以外）
                
                visited.add(next_char)
                current = next_char
                steps += 1
        
        return False  # 矛盾なし
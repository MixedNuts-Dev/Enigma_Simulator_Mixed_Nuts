class DiagonalBoard:
    """Diagonal board for efficient contradiction detection in plugboard hypotheses"""
    
    def __init__(self):
        self.connections = [set() for _ in range(26)]
    
    def test_hypothesis(self, wiring):
        """Test plugboard hypothesis and return True if there's a contradiction"""
        # Check for self-steckers
        if self.has_self_stecker(wiring):
            return True  # Contradiction found
        
        # Check for more complex contradictions
        return self.has_contradiction(wiring)
    
    def has_self_stecker(self, wiring):
        """Check if any character maps to itself"""
        for from_char, to_char in wiring.items():
            if from_char == to_char:
                return True  # Self-stecker detected
        return False
    
    def has_contradiction(self, wiring):
        """Efficient contradiction detection"""
        # Clear connections
        for conn in self.connections:
            conn.clear()
        
        # Build connection graph from wiring
        for from_char, to_char in wiring.items():
            from_idx = ord(from_char) - ord('A')
            to_idx = ord(to_char) - ord('A')
            
            # Add bidirectional connections
            self.connections[from_idx].add(to_char)
            self.connections[to_idx].add(from_char)
        
        # Check transitive closure
        return self._check_transitive_closure(wiring)
    
    def _check_transitive_closure(self, wiring):
        """Check for contradictions using Union-Find structure"""
        # Union-Find structure to track connected components
        parent = list(range(26))
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def unite(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Union based on wiring
        for from_char, to_char in wiring.items():
            from_idx = ord(from_char) - ord('A')
            to_idx = ord(to_char) - ord('A')
            unite(from_idx, to_idx)
        
        # Check component sizes
        components = {}
        for i in range(26):
            root = find(i)
            if root not in components:
                components[root] = set()
            components[root].add(i)
        
        # Check plugboard constraints
        for comp in components.values():
            # Odd-sized components are impossible (plugboard uses pairs only)
            if len(comp) % 2 != 0 and len(comp) > 1:
                return True  # Contradiction: odd-sized component
            
            # Check connection count for each character
            for idx in comp:
                ch = chr(ord('A') + idx)
                connection_count = 0
                
                # Count connections for this character
                for from_char, to_char in wiring.items():
                    if from_char == ch or to_char == ch:
                        connection_count += 1
                
                # In plugboard, each character has at most one connection
                if connection_count > 2:  # Bidirectional, so 2 max
                    return True  # Contradiction: multiple connections
        
        # Check for cycles (3+ character cycles are impossible)
        for start_char in wiring:
            current = wiring.get(start_char)
            steps = 1
            
            while current and current in wiring and steps < 3:
                current = wiring[current]
                steps += 1
                
                if current == start_char and steps > 2:
                    return True  # Contradiction: 3+ character cycle
        
        return False  # No contradiction
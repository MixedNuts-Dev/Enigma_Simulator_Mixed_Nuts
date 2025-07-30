package com.enigma.core;

import java.util.*;

public class DiagonalBoard {
    private List<Set<Character>> connections;
    
    public DiagonalBoard() {
        connections = new ArrayList<>(26);
        for (int i = 0; i < 26; i++) {
            connections.add(new HashSet<>());
        }
    }
    
    // プラグボード仮説をテストし、矛盾があればtrueを返す
    public boolean testHypothesis(Map<Character, Character> wiring) {
        // 自己ステッカーのチェック
        if (hasSelfStecker(wiring)) {
            return true;  // 矛盾あり
        }
        
        // より複雑な矛盾のチェック
        return hasContradiction(wiring);
    }
    
    // 単一の文字ペアをテストし、自己ステッカー（self-stecker）を検出
    public boolean hasSelfStecker(Map<Character, Character> wiring) {
        // 各文字が自分自身にマッピングされていないかチェック
        for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
            if (entry.getKey().equals(entry.getValue())) {
                return true;  // 自己ステッカーを検出
            }
        }
        return false;
    }
    
    // 効率的な矛盾検出のための高速チェック
    public boolean hasContradiction(Map<Character, Character> wiring) {
        // 入力が空の場合は矛盾なし
        if (wiring.isEmpty()) {
            return false;
        }
        
        // 接続をクリア
        for (Set<Character> conn : connections) {
            conn.clear();
        }
        
        // 配線から接続グラフを構築
        for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
            // 文字の範囲チェック
            if (entry.getKey() < 'A' || entry.getKey() > 'Z' || 
                entry.getValue() < 'A' || entry.getValue() > 'Z') {
                return true;  // 無効な文字
            }
            
            int from = entry.getKey() - 'A';
            int to = entry.getValue() - 'A';
            
            // インデックスの境界チェック
            if (from < 0 || from >= 26 || to < 0 || to >= 26) {
                return true;  // インデックスエラー
            }
            
            // 双方向の接続を追加
            connections.get(from).add(entry.getValue());
            connections.get(to).add(entry.getKey());
        }
        
        // 推移的閉包をチェック
        return checkTransitiveClosure(wiring);
    }
    
    private boolean checkTransitiveClosure(Map<Character, Character> wiring) {
        // Union-Find構造を使用して接続コンポーネントを追跡
        int[] parent = new int[26];
        for (int i = 0; i < 26; i++) {
            parent[i] = i;
        }
        
        // 配線に基づいてユニオン
        for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
            int from = entry.getKey() - 'A';
            int to = entry.getValue() - 'A';
            unite(parent, from, to);
        }
        
        // 各コンポーネントのサイズをチェック
        Map<Integer, Set<Integer>> components = new HashMap<>();
        for (int i = 0; i < 26; i++) {
            int root = find(parent, i);
            components.computeIfAbsent(root, k -> new HashSet<>()).add(i);
        }
        
        // プラグボードの制約をチェック
        for (Map.Entry<Integer, Set<Integer>> comp : components.entrySet()) {
            if (comp.getValue().size() % 2 != 0 && comp.getValue().size() > 1) {
                return true;  // 矛盾：奇数サイズのコンポーネント
            }
            
            // 各文字の接続数をチェック
            for (int idx : comp.getValue()) {
                char ch = (char)('A' + idx);
                int connectionCount = 0;
                
                // この文字の配線をカウント
                for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
                    if (entry.getKey() == ch || entry.getValue() == ch) {
                        connectionCount++;
                    }
                }
                
                // プラグボードでは各文字は最大1つの接続のみ
                if (connectionCount > 2) {  // 双方向なので2まで
                    return true;  // 矛盾：複数接続
                }
            }
        }
        
        // 循環をチェック（3文字以上の循環は不可）
        for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
            char start = entry.getKey();
            char current = entry.getValue();
            int steps = 1;
            
            // 訪問済みをトラックして無限ループを防ぐ
            Set<Character> visited = new HashSet<>();
            visited.add(start);
            visited.add(current);
            
            while (steps < 26) {  // 最大26文字まで
                Character next = wiring.get(current);
                if (next == null) {
                    break;  // マッピングが見つからない場合は終了
                }
                
                if (next == start && steps > 2) {
                    return true;  // 矛盾：3文字以上の循環
                }
                
                if (visited.contains(next) && next != start) {
                    break;  // 既に訪問済み（start以外）
                }
                
                visited.add(next);
                current = next;
                steps++;
            }
        }
        
        return false;  // 矛盾なし
    }
    
    private int find(int[] parent, int x) {
        if (parent[x] != x) {
            parent[x] = find(parent, parent[x]);
        }
        return parent[x];
    }
    
    private void unite(int[] parent, int x, int y) {
        int px = find(parent, x);
        int py = find(parent, y);
        if (px != py) {
            parent[px] = py;
        }
    }
}
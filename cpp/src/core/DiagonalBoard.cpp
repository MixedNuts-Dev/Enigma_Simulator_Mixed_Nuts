#include "DiagonalBoard.h"
#include <algorithm>
#include <functional>

DiagonalBoard::DiagonalBoard() : connections_(26) {
}

bool DiagonalBoard::testHypothesis(const std::map<char, char>& wiring) {
    // 自己ステッカーのチェック
    if (hasSelfStecker(wiring)) {
        return true;  // 矛盾あり
    }
    
    // より複雑な矛盾のチェック
    return hasContradiction(wiring);
}

bool DiagonalBoard::hasSelfStecker(const std::map<char, char>& wiring) {
    // 各文字が自分自身にマッピングされていないかチェック
    for (const auto& pair : wiring) {
        if (pair.first == pair.second) {
            return true;  // 自己ステッカーを検出
        }
    }
    return false;
}

bool DiagonalBoard::hasContradiction(const std::map<char, char>& wiring) {
    // 接続をクリア
    for (auto& conn : connections_) {
        conn.clear();
    }
    
    // 配線から接続グラフを構築
    for (const auto& pair : wiring) {
        int from = pair.first - 'A';
        int to = pair.second - 'A';
        
        // 双方向の接続を追加
        connections_[from].insert(pair.second);
        connections_[to].insert(pair.first);
    }
    
    // 推移的閉包をチェック
    return checkTransitiveClosure(wiring);
}

bool DiagonalBoard::checkTransitiveClosure(const std::map<char, char>& wiring) {
    // Union-Find構造を使用して接続コンポーネントを追跡
    std::vector<int> parent(26);
    for (int i = 0; i < 26; i++) {
        parent[i] = i;
    }
    
    // Find関数（パス圧縮付き）
    std::function<int(int)> find = [&](int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]);
        }
        return parent[x];
    };
    
    // Union関数
    auto unite = [&](int x, int y) {
        int px = find(x);
        int py = find(y);
        if (px != py) {
            parent[px] = py;
        }
    };
    
    // 配線に基づいてユニオン
    for (const auto& pair : wiring) {
        int from = pair.first - 'A';
        int to = pair.second - 'A';
        unite(from, to);
    }
    
    // 各コンポーネントのサイズをチェック
    std::map<int, std::set<int>> components;
    for (int i = 0; i < 26; i++) {
        components[find(i)].insert(i);
    }
    
    // プラグボードの制約をチェック：
    // 1. 各文字は最大1つの他の文字と接続
    // 2. 接続は相互的（AがBに接続ならBもAに接続）
    // 3. 奇数サイズのコンポーネントは不可能（プラグボードはペアのみ）
    for (const auto& comp : components) {
        if (comp.second.size() % 2 != 0 && comp.second.size() > 1) {
            return true;  // 矛盾：奇数サイズのコンポーネント
        }
        
        // 各文字の接続数をチェック
        for (int idx : comp.second) {
            char ch = 'A' + idx;
            int connectionCount = 0;
            
            // この文字の配線をカウント
            for (const auto& pair : wiring) {
                if (pair.first == ch || pair.second == ch) {
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
    for (const auto& pair : wiring) {
        char start = pair.first;
        char current = pair.second;
        int steps = 1;
        
        while (wiring.find(current) != wiring.end() && steps < 3) {
            current = wiring.at(current);
            steps++;
            
            if (current == start && steps > 2) {
                return true;  // 矛盾：3文字以上の循環
            }
        }
    }
    
    return false;  // 矛盾なし
}
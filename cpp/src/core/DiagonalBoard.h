#ifndef DIAGONAL_BOARD_H
#define DIAGONAL_BOARD_H

#include <vector>
#include <map>
#include <set>

class DiagonalBoard {
public:
    DiagonalBoard();
    
    // プラグボード仮説をテストし、矛盾があればtrueを返す
    bool testHypothesis(const std::map<char, char>& wiring);
    
    // 単一の文字ペアをテストし、自己ステッカー（self-stecker）を検出
    bool hasSelfStecker(const std::map<char, char>& wiring);
    
    // 効率的な矛盾検出のための高速チェック
    bool hasContradiction(const std::map<char, char>& wiring);
    
private:
    // 各文字の接続状態を追跡
    std::vector<std::set<char>> connections_;
    
    // 推移的閉包を計算して矛盾を検出
    bool checkTransitiveClosure(const std::map<char, char>& wiring);
};

#endif // DIAGONAL_BOARD_H
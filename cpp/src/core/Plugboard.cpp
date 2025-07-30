#include "Plugboard.h"
#include <algorithm>
#include <stdexcept>

Plugboard::Plugboard() {}

Plugboard::Plugboard(const std::vector<std::string>& pairs) {
    // 最大10組の制限をチェック
    if (pairs.size() > MAX_PAIRS) {
        throw std::invalid_argument("プラグボード接続数は最大" + std::to_string(MAX_PAIRS) + 
                                   "組までです。" + std::to_string(pairs.size()) + 
                                   "組が指定されました。");
    }
    
    for (const auto& pair : pairs) {
        if (pair.length() == 2) {
            addPair(pair[0], pair[1]);
        }
    }
}

Plugboard::Plugboard(const std::vector<std::pair<char, char>>& pairs) {
    // 最大10組の制限をチェック
    if (pairs.size() > MAX_PAIRS) {
        throw std::invalid_argument("プラグボード接続数は最大" + std::to_string(MAX_PAIRS) + 
                                   "組までです。" + std::to_string(pairs.size()) + 
                                   "組が指定されました。");
    }
    
    for (const auto& pair : pairs) {
        addPair(pair.first, pair.second);
    }
}

char Plugboard::swap(char c) const {
    auto it = mapping_.find(c);
    return (it != mapping_.end()) ? it->second : c;
}

bool Plugboard::addPair(char a, char b) {
    // Check if either character is already mapped
    if (mapping_.find(a) != mapping_.end() || mapping_.find(b) != mapping_.end()) {
        return false;
    }
    
    // 最大10組の制限をチェック
    if (mapping_.size() / 2 >= MAX_PAIRS) {
        return false;
    }
    
    mapping_[a] = b;
    mapping_[b] = a;
    return true;
}

void Plugboard::clear() {
    mapping_.clear();
}

std::vector<std::string> Plugboard::getPairs() const {
    std::vector<std::string> pairs;
    std::unordered_map<char, bool> seen;
    
    for (const auto& [a, b] : mapping_) {
        if (!seen[a] && !seen[b]) {
            std::string pair;
            pair += std::min(a, b);
            pair += std::max(a, b);
            pairs.push_back(pair);
            seen[a] = seen[b] = true;
        }
    }
    
    return pairs;
}
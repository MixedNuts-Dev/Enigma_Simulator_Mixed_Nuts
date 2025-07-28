#include "Plugboard.h"
#include <algorithm>

Plugboard::Plugboard() {}

Plugboard::Plugboard(const std::vector<std::string>& pairs) {
    for (const auto& pair : pairs) {
        if (pair.length() == 2) {
            addPair(pair[0], pair[1]);
        }
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
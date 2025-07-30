#ifndef PLUGBOARD_H
#define PLUGBOARD_H

#include <string>
#include <vector>
#include <unordered_map>

class Plugboard {
public:
    static constexpr int MAX_PAIRS = 10; // 史実のエニグマでは最大10組までの接続が可能
    
    Plugboard();
    explicit Plugboard(const std::vector<std::string>& pairs);
    explicit Plugboard(const std::vector<std::pair<char, char>>& pairs);
    
    char swap(char c) const;
    bool addPair(char a, char b);
    void clear();
    std::vector<std::string> getPairs() const;
    
private:
    std::unordered_map<char, char> mapping_;
};

#endif // PLUGBOARD_H
#ifndef PLUGBOARD_H
#define PLUGBOARD_H

#include <string>
#include <vector>
#include <unordered_map>

class Plugboard {
public:
    Plugboard();
    explicit Plugboard(const std::vector<std::string>& pairs);
    
    char swap(char c) const;
    bool addPair(char a, char b);
    void clear();
    std::vector<std::string> getPairs() const;
    
private:
    std::unordered_map<char, char> mapping_;
};

#endif // PLUGBOARD_H
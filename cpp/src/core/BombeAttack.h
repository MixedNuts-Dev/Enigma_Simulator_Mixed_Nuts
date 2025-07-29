#pragma once
#include <string>
#include <vector>
#include <functional>
#include <atomic>
#include <mutex>
#include <future>
#include <map>
#include <set>

struct CandidateResult {
    double score;
    std::vector<int> positions;
    std::vector<std::string> rotorOrder;
    std::vector<std::pair<char, char>> plugboard;
    double matchRate;
    int plugboardPairs;
    int offset;
    
    bool operator<(const CandidateResult& other) const {
        return score > other.score; // Descending order
    }
    
    std::string getPositionString() const;
    std::string getRotorString() const;
};

class BombeAttack {
public:
    BombeAttack(const std::string& cribText, 
                const std::string& cipherText,
                const std::vector<std::string>& rotorTypes,
                const std::string& reflectorType,
                bool testAllOrders = false,
                bool searchWithoutPlugboard = false);
    
    std::vector<CandidateResult> attack(
        std::function<void(const std::string&)> progressCallback = nullptr);
    
    void stop() { stopFlag_ = true; }
    
private:
    std::string cribText_;
    std::string cipherText_;
    std::vector<std::string> rotorTypes_;
    std::string reflectorType_;
    bool testAllOrders_;
    bool searchWithoutPlugboard_;
    
    std::atomic<bool> stopFlag_{false};
    std::mutex resultsMutex_;
    std::vector<CandidateResult> results_;
    bool hasPlugboardConflict_ = false;
    std::function<void(const std::string&)> progressCallback_;
    
    void testPosition(const std::vector<int>& positions,
                     const std::vector<std::string>& rotorOrder,
                     int offset);
    
    std::vector<std::pair<char, char>> deducePlugboardWiring(
        const std::vector<int>& positions,
        const std::vector<std::string>& rotorOrder,
        int offset);
    
    bool propagateConstraints(
        std::map<char, char>& wiring,
        char from,
        char to);
    
    std::vector<char> traceThroughEnigma(
        const std::vector<int>& positions,
        const std::vector<std::string>& rotorOrder,
        int startOffset,
        const std::string& input);
    
    std::vector<std::vector<std::string>> generatePermutations(
        const std::vector<std::string>& items);
};
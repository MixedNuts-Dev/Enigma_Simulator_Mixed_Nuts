#pragma once
#include <string>
#include <vector>
#include <functional>
#include <atomic>
#include <mutex>
#include <future>
#include <map>
#include <set>
#include <thread>
#include <chrono>
#include "DiagonalBoard.h"

#ifdef USE_OPENCL
#include <CL/cl.h>
#endif

#ifdef USE_CUDA
#include <cuda_runtime.h>
#endif

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
    
    ~BombeAttack();
    
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
    mutable std::mutex diagonalBoardMutex_;
    DiagonalBoard diagonalBoard_;
    
    // CPU負荷管理
    std::atomic<double> cpuUsage_{0.0};
    std::atomic<int> activeThreads_{0};
    int maxThreads_;
    std::chrono::milliseconds threadDelay_{0};
    
    // GPU処理用
    bool useGPU_ = false;
    void* gpuContext_ = nullptr;
    
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
    
    // 史実のBombeアルゴリズム用の追加メソッド
    struct MenuLink {
        int position;     // クリブ内の位置
        char fromChar;    // 変換元の文字
        char toChar;      // 変換先の文字
    };
    
    std::vector<MenuLink> createMenu();
    
    std::map<char, std::set<char>> findLoops(const std::vector<MenuLink>& menu);
    
    bool testPlugboardHypothesis(
        const std::vector<int>& positions,
        const std::vector<std::string>& rotorOrder,
        int offset,
        char assumedStecker,
        std::map<char, char>& deducedSteckers);
    
    void propagateStecker(
        char letter,
        char stecker,
        const std::vector<MenuLink>& menu,
        std::map<char, char>& steckerboard,
        bool& contradiction);
    
    // CPU負荷管理
    double getCPUUsage();
    void adjustThreadCount();
    void throttleIfNeeded();
    
    // GPU処理
    bool initializeGPU();
    void cleanupGPU();
    bool processOnGPU(const std::vector<std::vector<int>>& positionBatch,
                      const std::vector<std::string>& rotorOrder,
                      int offset);
};
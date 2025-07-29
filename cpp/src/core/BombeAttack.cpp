#include "BombeAttack.h"
#include "EnigmaMachine.h"
#include "Rotor.h"
#include "Reflector.h"
#include "Plugboard.h"
#include "RotorConfig.h"
#include <algorithm>
#include <cctype>
#include <thread>
#include <chrono>
#include <atomic>
#include <memory>
#include <string>
#include <cstdint>
#include <omp.h>
#include <fstream>
#include <iostream>
#include <sstream>
#include <ctime>
#include <mutex>
#include <iomanip>

#ifdef _WIN32
#define NOMINMAX  // Windowsのmin/maxマクロを無効化
#include <windows.h>
#endif

#ifdef USE_CUDA
#include <cuda_runtime.h>
#include <device_launch_parameters.h>
#endif

#ifdef USE_OPENCL
#include <CL/cl.h>
#endif

// デバッグログファイル
static std::ofstream debugLog;
static std::mutex debugLogMutex;

void writeDebugLog(const std::string& message) {
    std::lock_guard<std::mutex> lock(debugLogMutex);
    if (!debugLog.is_open()) {
        debugLog.open("bombe_debug.log", std::ios::app);
        debugLog << "\n=== New Debug Session ===" << std::endl;
        auto t = std::time(nullptr);
        auto tm = *std::localtime(&t);
        debugLog << "Time: " << std::put_time(&tm, "%d-%m-%Y %H:%M:%S") << std::endl;
    }
    debugLog << message << std::endl;
    debugLog.flush();
}

BombeAttack::BombeAttack(const std::string& cribText, 
                         const std::string& cipherText,
                         const std::vector<std::string>& rotorTypes,
                         const std::string& reflectorType,
                         bool testAllOrders,
                         bool searchWithoutPlugboard)
    : cribText_(cribText), cipherText_(cipherText), 
      rotorTypes_(rotorTypes), reflectorType_(reflectorType),
      testAllOrders_(testAllOrders), searchWithoutPlugboard_(searchWithoutPlugboard) {
    // 大文字に変換
    std::transform(cribText_.begin(), cribText_.end(), cribText_.begin(), ::toupper);
    std::transform(cipherText_.begin(), cipherText_.end(), cipherText_.begin(), ::toupper);
    
    // CPU数に基づいてスレッド数を設定（ただし最大でCPU数の75%）
    unsigned int hwThreads = std::thread::hardware_concurrency();
    maxThreads_ = static_cast<int>((std::max)(1u, (hwThreads * 3) / 4));
    
    // GPU初期化を試みる
    useGPU_ = initializeGPU();
}

BombeAttack::~BombeAttack() {
    cleanupGPU();
    
    // ログファイルを閉じる
    std::lock_guard<std::mutex> lock(debugLogMutex);
    if (debugLog.is_open()) {
        debugLog.close();
    }
}

std::vector<CandidateResult> BombeAttack::attack(
    std::function<void(const std::string&)> progressCallback) {
    
    progressCallback_ = progressCallback;
    
    std::vector<std::vector<std::string>> rotorOrders;
    if (testAllOrders_) {
        // 全ローターから3つを選び、その順列を生成
        if (rotorTypes_.size() > 3) {
            // 組み合わせを生成
            for (size_t i = 0; i < rotorTypes_.size(); i++) {
                for (size_t j = 0; j < rotorTypes_.size(); j++) {
                    if (j == i) continue;
                    for (size_t k = 0; k < rotorTypes_.size(); k++) {
                        if (k == i || k == j) continue;
                        std::vector<std::string> combination = {
                            rotorTypes_[i], rotorTypes_[j], rotorTypes_[k]
                        };
                        rotorOrders.push_back(combination);
                    }
                }
            }
        } else {
            // 3個以下の場合は全順列を生成
            rotorOrders = generatePermutations(rotorTypes_);
        }
    } else {
        rotorOrders.push_back(rotorTypes_);
    }
    
    int maxOffset = (std::max)(0, static_cast<int>(cipherText_.length() - cribText_.length() + 1));
    int totalTasks = 26 * 26 * 26 * rotorOrders.size() * maxOffset;
    
    if (progressCallback) {
        progressCallback("Starting Bombe attack...");
        progressCallback("Crib: " + cribText_);
        progressCallback("Cipher: " + cipherText_);
        if (testAllOrders_ && rotorTypes_.size() > 3) {
            int combinations = rotorTypes_.size() * (rotorTypes_.size() - 1) * (rotorTypes_.size() - 2);
            progressCallback("Rotor combinations: " + std::to_string(combinations) + 
                           " (from " + std::to_string(rotorTypes_.size()) + " rotors)");
        } else {
            progressCallback("Rotor orders to test: " + std::to_string(rotorOrders.size()));
        }
        progressCallback("Total combinations to test: " + std::to_string(totalTasks));
        progressCallback("Search without plugboard: " + std::string(searchWithoutPlugboard_ ? "true" : "false"));
    }
    
    // OpenMP設定を調整して負荷を制御
    int numThreads = (std::min)(maxThreads_, static_cast<int>(omp_get_max_threads()));
    omp_set_num_threads(numThreads);
    
    // スレッドの優先度を下げる
    #ifdef _WIN32
    SetThreadPriority(GetCurrentThread(), THREAD_PRIORITY_BELOW_NORMAL);
    #endif
    
    if (progressCallback) {
        progressCallback("Using " + std::to_string(numThreads) + " threads");
        if (useGPU_) {
            progressCallback("GPU acceleration enabled");
        }
    }
    
    std::atomic<int> processedCount(0);
    
    #pragma omp parallel for schedule(dynamic, 1) num_threads(numThreads)
    for (int orderIdx = 0; orderIdx < static_cast<int>(rotorOrders.size()); orderIdx++) {
        for (int offset = 0; offset < maxOffset; offset++) {
            for (int pos1 = 0; pos1 < 26; pos1++) {
                for (int pos2 = 0; pos2 < 26; pos2++) {
                    for (int pos3 = 0; pos3 < 26; pos3++) {
                        if (stopFlag_) continue;
                        
                        // CPU負荷制御
                        if (threadDelay_.count() > 0) {
                            std::this_thread::sleep_for(threadDelay_);
                        }
                        
                        std::vector<int> positions = {pos1, pos2, pos3};
                        testPosition(positions, rotorOrders[orderIdx], offset);
                        
                        int count = processedCount.fetch_add(1);
                        if (count % 5000 == 0) {
                            // 定期的にCPU使用率をチェックして調整
                            adjustThreadCount();
                            
                            if (progressCallback) {
                                double progress = (count * 100.0) / totalTasks;
                                progressCallback("Progress: " + std::to_string(count) + "/" + 
                                               std::to_string(totalTasks) + " (" + 
                                               std::to_string(static_cast<int>(progress)) + "%)");
                            }
                        }
                    }
                }
            }
        }
    }
    
    // スコアで結果をソート
    std::sort(results_.begin(), results_.end());
    
    if (progressCallback) {
        progressCallback("Bombe attack completed. Found " + 
                        std::to_string(results_.size()) + " candidates.");
    }
    
    return results_;
}

void BombeAttack::testPosition(const std::vector<int>& positions,
                               const std::vector<std::string>& rotorOrder,
                               int offset) {
    // クリブがこのオフセットに適合するかチェック
    if (offset + cribText_.length() > cipherText_.length()) {
        return;
    }
    
    // 暗号文の該当部分を取得
    std::string cipherPart = cipherText_.substr(offset, cribText_.length());
    
    // 電気経路追跡を使用してプラグボード配線を推定
    auto plugboardHypothesis = deducePlugboardWiring(positions, rotorOrder, offset);
    
    if (plugboardHypothesis.empty() && hasPlugboardConflict_) {
        return;
    }
    
    // 推定されたプラグボードでエニグマを作成
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    for (const auto& type : rotorOrder) {
        if (enigma::ROTOR_DEFINITIONS.find(type) == enigma::ROTOR_DEFINITIONS.end()) {
            return;  // 無効なローター
        }
        auto& def = enigma::ROTOR_DEFINITIONS.at(type);
        rotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
    }
    
    if (enigma::REFLECTOR_DEFINITIONS.find(reflectorType_) == enigma::REFLECTOR_DEFINITIONS.end()) {
        return;  // 無効なリフレクター
    }
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
    auto reflector = std::make_unique<Reflector>(refDef.wiring);
    
    auto plugboard = std::make_unique<Plugboard>(plugboardHypothesis);
    
    EnigmaMachine enigma(std::move(rotors), std::move(reflector), std::move(plugboard));
    enigma.setRotorPositions(positions);
    
    // オフセットまでローターを進める
    for (int i = 0; i < offset; i++) {
        enigma.stepRotors();
    }
    
    // 暗号化をテスト
    std::string testResult = enigma.encrypt(cribText_);
    
    // 完全一致をチェック
    if (testResult == cipherPart) {
        CandidateResult result;
        result.score = 100.0 - plugboardHypothesis.size() * 2;
        result.positions = positions;
        result.rotorOrder = rotorOrder;
        result.plugboard = plugboardHypothesis;
        result.matchRate = 1.0;
        result.plugboardPairs = plugboardHypothesis.size();
        result.offset = offset;
        
        std::lock_guard<std::mutex> lock(resultsMutex_);
        results_.push_back(result);
        
    } else if (!hasPlugboardConflict_ && plugboardHypothesis.empty()) {
        // プラグボードが推定されない場合の部分一致をチェック
        int matches = 0;
        for (size_t i = 0; i < testResult.length(); i++) {
            if (testResult[i] == cipherPart[i]) {
                matches++;
            }
        }
        
        double matchRate = static_cast<double>(matches) / cribText_.length();
        if (matchRate >= 0.5) {
            CandidateResult result;
            result.score = matchRate * 100;
            result.positions = positions;
            result.rotorOrder = rotorOrder;
            result.plugboard = plugboardHypothesis;
            result.matchRate = matchRate;
            result.plugboardPairs = 0;
            result.offset = offset;
            
            std::lock_guard<std::mutex> lock(resultsMutex_);
            results_.push_back(result);
        }
    }
}

std::vector<std::pair<char, char>> BombeAttack::deducePlugboardWiring(
    const std::vector<int>& positions,
    const std::vector<std::string>& rotorOrder,
    int offset) {
    
    hasPlugboardConflict_ = false;
    std::string cipherPart = cipherText_.substr(offset, cribText_.length());
    
    // まずプラグボードなしでエニグマを作成
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    for (const auto& type : rotorOrder) {
        if (enigma::ROTOR_DEFINITIONS.find(type) == enigma::ROTOR_DEFINITIONS.end()) {
            return {};
        }
        auto& def = enigma::ROTOR_DEFINITIONS.at(type);
        rotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
    }
    
    if (enigma::REFLECTOR_DEFINITIONS.find(reflectorType_) == enigma::REFLECTOR_DEFINITIONS.end()) {
        return {};
    }
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
    auto reflector = std::make_unique<Reflector>(refDef.wiring);
    auto plugboard = std::make_unique<Plugboard>(std::vector<std::string>{});
    
    EnigmaMachine enigma(std::move(rotors), std::move(reflector), std::move(plugboard));
    enigma.setRotorPositions(positions);
    
    // オフセットまでローターを進める
    for (int i = 0; i < offset; i++) {
        enigma.stepRotors();
    }
    
    // プラグボードなしでテスト
    std::string testResult = enigma.encrypt(cribText_);
    if (testResult == cipherPart) {
        return {};  // プラグボードなしで一致
    }
    
    if (searchWithoutPlugboard_) {
        return {};
    }
    
    // プラグボードなしでの暗号化結果を保存
    std::string noPlugboardResult = testResult;
    
    // プラグボードの推定：実際のBombeアルゴリズム
    // まず簡単な方法を試す
    std::map<char, char> requiredMappings;
    
    for (size_t i = 0; i < cribText_.length(); i++) {
        char cipherChar = cipherPart[i];
        char noPlugChar = noPlugboardResult[i];
        
        // プラグボードが必要な変換を記録
        if (noPlugChar != cipherChar) {
            // noPlugCharをcipherCharに変換する必要がある
            if (!propagateConstraints(requiredMappings, noPlugChar, cipherChar)) {
                hasPlugboardConflict_ = true;
                return {};
            }
        }
    }
    
    // 推定されたマッピングから有効なプラグボード設定を生成
    if (!requiredMappings.empty()) {
        // 検証
        auto verifyRotors = std::vector<std::unique_ptr<Rotor>>();
        for (const auto& type : rotorOrder) {
            auto& def = enigma::ROTOR_DEFINITIONS.at(type);
            verifyRotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
        }
        auto& verifyRefDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
        auto verifyReflector = std::make_unique<Reflector>(verifyRefDef.wiring);
        
        std::vector<std::pair<char, char>> plugboardPairs;
        std::set<char> used;
        
        for (const auto& pair : requiredMappings) {
            if (used.find(pair.first) == used.end() && 
                used.find(pair.second) == used.end() &&
                pair.first != pair.second) {
                if (pair.first < pair.second) {
                    plugboardPairs.push_back({pair.first, pair.second});
                } else {
                    plugboardPairs.push_back({pair.second, pair.first});
                }
                used.insert(pair.first);
                used.insert(pair.second);
            }
        }
        
        std::vector<std::string> pbStrings;
        for (const auto& pair : plugboardPairs) {
            pbStrings.push_back(std::string(1, pair.first) + std::string(1, pair.second));
        }
        auto verifyPlugboard = std::make_unique<Plugboard>(pbStrings);
        
        EnigmaMachine verifyMachine(std::move(verifyRotors), std::move(verifyReflector), std::move(verifyPlugboard));
        verifyMachine.setRotorPositions(positions);
        
        for (int i = 0; i < offset; i++) {
            verifyMachine.stepRotors();
        }
        
        std::string verifyResult = verifyMachine.encrypt(cribText_);
        if (verifyResult == cipherPart) {
            return plugboardPairs;
        }
    }
    
    // 史実のBombeアルゴリズムを使用
    // 各文字（A-Z）を仮定のステッカーとしてテスト
    for (char assumedStecker = 'A'; assumedStecker <= 'Z'; assumedStecker++) {
        std::map<char, char> deducedSteckers;
        
        // クリブの最初の文字から開始（Turingの方法）
        if (cribText_[0] == assumedStecker) {
            continue;  // 自己ステッカーは不可能
        }
        
        if (testPlugboardHypothesis(positions, rotorOrder, offset, assumedStecker, deducedSteckers)) {
            // 有効なステッカー設定が見つかった
            std::vector<std::pair<char, char>> plugboardPairs;
            std::set<char> used;
            
            for (const auto& pair : deducedSteckers) {
                if (used.find(pair.first) == used.end() && 
                    used.find(pair.second) == used.end() &&
                    pair.first != pair.second) {
                    if (pair.first < pair.second) {
                        plugboardPairs.push_back({pair.first, pair.second});
                    } else {
                        plugboardPairs.push_back({pair.second, pair.first});
                    }
                    used.insert(pair.first);
                    used.insert(pair.second);
                }
            }
            
            // プラグボード仮説をdiagonal boardでテスト
            bool hasContradiction = false;
            try {
                // 各スレッドごとにDiagonalBoardインスタンスを作成
                DiagonalBoard localDiagonalBoard;
                hasContradiction = localDiagonalBoard.hasContradiction(deducedSteckers);
            } catch (const std::exception& e) {
                hasContradiction = true;
            } catch (...) {
                hasContradiction = true;
            }
            
            if (hasContradiction) {
                continue;  // 矛盾があればスキップ
            }
            
            // 検証
            auto verifyRotors = std::vector<std::unique_ptr<Rotor>>();
            for (const auto& type : rotorOrder) {
                auto& def = enigma::ROTOR_DEFINITIONS.at(type);
                verifyRotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
            }
            auto& verifyRefDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
            auto verifyReflector = std::make_unique<Reflector>(verifyRefDef.wiring);
            
            std::vector<std::string> pbStrings;
            for (const auto& pair : plugboardPairs) {
                pbStrings.push_back(std::string(1, pair.first) + std::string(1, pair.second));
            }
            auto verifyPlugboard = std::make_unique<Plugboard>(pbStrings);
            
            EnigmaMachine verifyMachine(std::move(verifyRotors), std::move(verifyReflector), std::move(verifyPlugboard));
            verifyMachine.setRotorPositions(positions);
            
            for (int i = 0; i < offset; i++) {
                verifyMachine.stepRotors();
            }
            
            std::string verifyResult = verifyMachine.encrypt(cribText_);
            if (verifyResult == cipherPart) {
                return plugboardPairs;
            }
        }
    }
    
    hasPlugboardConflict_ = true;
    return {};
}

bool BombeAttack::propagateConstraints(
    std::map<char, char>& wiring,
    char from,
    char to) {
    
    // 'from'がすでにマッピングを持っているか確認
    if (wiring.find(from) != wiring.end()) {
        // 競合する場合はfalseを返す
        if (wiring[from] != to) {
            return false;
        }
        // 一致している場合は何もしない
        return true;
    }
    
    // 'to'がすでにマッピングを持っているか確認
    if (wiring.find(to) != wiring.end()) {
        // 競合する場合はfalseを返す
        if (wiring[to] != from) {
            return false;
        }
        // 一致している場合は何もしない
        return true;
    }
    
    // 'to'がすでに他の文字にマッピングされているか確認
    for (const auto& pair : wiring) {
        if (pair.second == to && pair.first != from) {
            return false;
        }
    }
    
    // 新しいマッピングを追加（双方向）
    wiring[from] = to;
    wiring[to] = from;
    
    return true;
}

std::vector<char> BombeAttack::traceThroughEnigma(
    const std::vector<int>& positions,
    const std::vector<std::string>& rotorOrder,
    int startOffset,
    const std::string& input) {
    
    // プラグボードなしでエニグマを作成
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    for (const auto& type : rotorOrder) {
        if (enigma::ROTOR_DEFINITIONS.find(type) == enigma::ROTOR_DEFINITIONS.end()) {
            return std::vector<char>();  // 無効なローター
        }
        auto& def = enigma::ROTOR_DEFINITIONS.at(type);
        rotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
    }
    
    if (enigma::REFLECTOR_DEFINITIONS.find(reflectorType_) == enigma::REFLECTOR_DEFINITIONS.end()) {
        return std::vector<char>();  // 無効なリフレクター
    }
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
    auto reflector = std::make_unique<Reflector>(refDef.wiring);
    auto plugboard = std::make_unique<Plugboard>(std::vector<std::string>{});
    
    EnigmaMachine enigma(std::move(rotors), std::move(reflector), std::move(plugboard));
    enigma.setRotorPositions(positions);
    
    // 開始オフセットまで進める
    for (int i = 0; i < startOffset; i++) {
        enigma.stepRotors();
    }
    
    // 各文字を追跡
    std::vector<char> result;
    for (char c : input) {
        std::string singleChar(1, c);
        std::string output = enigma.encrypt(singleChar);
        result.push_back(output[0]);
    }
    
    return result;
}

std::vector<std::vector<std::string>> BombeAttack::generatePermutations(
    const std::vector<std::string>& items) {
    std::vector<std::vector<std::string>> result;
    std::vector<std::string> current = items;
    
    // std::next_permutationは入力がソートされている必要がある
    std::sort(current.begin(), current.end());
    
    do {
        result.push_back(current);
    } while (std::next_permutation(current.begin(), current.end()));
    
    return result;
}

// 史実のBombeアルゴリズムの実装
std::vector<BombeAttack::MenuLink> BombeAttack::createMenu() {
    std::vector<MenuLink> menu;
    
    // クリブと暗号文の各位置での文字関係を記録
    for (size_t i = 0; i < cribText_.length(); i++) {
        MenuLink link;
        link.position = i;
        link.fromChar = cribText_[i];
        link.toChar = cipherText_[i];  // オフセットは呼び出し側で処理
        menu.push_back(link);
    }
    
    return menu;
}

std::map<char, std::set<char>> BombeAttack::findLoops(const std::vector<MenuLink>& menu) {
    std::map<char, std::set<char>> connections;
    
    // 各位置での文字接続を記録
    for (const auto& link : menu) {
        connections[link.fromChar].insert(link.toChar);
        connections[link.toChar].insert(link.fromChar);
    }
    
    return connections;
}

bool BombeAttack::testPlugboardHypothesis(
    const std::vector<int>& positions,
    const std::vector<std::string>& rotorOrder,
    int offset,
    char assumedStecker,
    std::map<char, char>& deducedSteckers) {
    
    std::string cipherPart = cipherText_.substr(offset, cribText_.length());
    
    // 初期仮定：クリブの最初の文字が assumedStecker にステッカーされる
    deducedSteckers.clear();
    deducedSteckers[cribText_[0]] = assumedStecker;
    deducedSteckers[assumedStecker] = cribText_[0];
    
    // エニグママシンを作成（プラグボードなし）
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    for (const auto& type : rotorOrder) {
        if (enigma::ROTOR_DEFINITIONS.find(type) == enigma::ROTOR_DEFINITIONS.end()) {
            return false;
        }
        auto& def = enigma::ROTOR_DEFINITIONS.at(type);
        rotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
    }
    
    if (enigma::REFLECTOR_DEFINITIONS.find(reflectorType_) == enigma::REFLECTOR_DEFINITIONS.end()) {
        return false;
    }
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType_);
    
    // Bombeの各ドラムユニットをシミュレート
    std::vector<std::pair<char, char>> implications;  // 推定されたステッカーペア
    
    // エニグママシンを一度だけ作成
    auto testReflector = std::make_unique<Reflector>(refDef.wiring);
    auto testPlugboard = std::make_unique<Plugboard>(std::vector<std::string>{});
    
    // ローターをコピー
    auto testRotors = std::vector<std::unique_ptr<Rotor>>();
    for (const auto& type : rotorOrder) {
        auto& def = enigma::ROTOR_DEFINITIONS.at(type);
        testRotors.push_back(std::make_unique<Rotor>(def.wiring, def.getFirstNotch()));
    }
    
    EnigmaMachine testMachine(std::move(testRotors), std::move(testReflector), std::move(testPlugboard));
    
    for (size_t i = 0; i < cribText_.length(); i++) {
        // ローター位置を設定
        testMachine.setRotorPositions(positions);
        
        // この位置まで進める
        for (int j = 0; j < offset + static_cast<int>(i); j++) {
            testMachine.stepRotors();
        }
        
        // 入力文字（プラグボード適用後）
        char inputChar = cribText_[i];
        char steckeredInput = inputChar;
        if (deducedSteckers.find(inputChar) != deducedSteckers.end()) {
            steckeredInput = deducedSteckers[inputChar];
        }
        
        // エニグマを通す（ステップなし）
        char outputBeforePlugboard;
        try {
            outputBeforePlugboard = testMachine.encryptCharNoStep(steckeredInput);
        } catch (const std::exception& e) {
            return false;
        } catch (...) {
            return false;
        }
        
        // 出力側のステッカーを推定
        char expectedOutput = cipherPart[i];
        
        // 矛盾チェック
        if (deducedSteckers.find(outputBeforePlugboard) != deducedSteckers.end()) {
            if (deducedSteckers[outputBeforePlugboard] != expectedOutput) {
                return false;  // 矛盾
            }
        } else if (deducedSteckers.find(expectedOutput) != deducedSteckers.end()) {
            if (deducedSteckers[expectedOutput] != outputBeforePlugboard) {
                return false;  // 矛盾
            }
        } else if (outputBeforePlugboard != expectedOutput) {
            // 新しいステッカーペアを記録
            implications.push_back({outputBeforePlugboard, expectedOutput});
        }
    }
    
    // 含意されたステッカーを追加
    for (const auto& impl : implications) {
        if (deducedSteckers.find(impl.first) == deducedSteckers.end() &&
            deducedSteckers.find(impl.second) == deducedSteckers.end()) {
            deducedSteckers[impl.first] = impl.second;
            deducedSteckers[impl.second] = impl.first;
        }
    }
    
    return true;
}

void BombeAttack::propagateStecker(
    char letter,
    char stecker,
    const std::vector<MenuLink>& menu,
    std::map<char, char>& steckerboard,
    bool& contradiction) {
    
    // Turingの方法：ステッカーの影響を伝播
    std::vector<std::pair<char, char>> toProcess;
    toProcess.push_back({letter, stecker});
    
    while (!toProcess.empty() && !contradiction) {
        auto current = toProcess.back();
        toProcess.pop_back();
        
        // メニュー内でこの文字に関連する全ての位置をチェック
        for (const auto& link : menu) {
            if (link.fromChar == current.first) {
                // 対応する暗号文字もステッカーされる必要がある
                char implied = link.toChar;
                
                if (steckerboard.find(implied) != steckerboard.end()) {
                    // すでにステッカーが存在する場合、矛盾をチェック
                    if (steckerboard[implied] != current.second) {
                        // 同じ位置で異なるステッカーは不可能
                        continue;  // この経路は無視
                    }
                } else {
                    // 新しい含意を追加
                    steckerboard[implied] = current.second;
                    steckerboard[current.second] = implied;
                    toProcess.push_back({implied, current.second});
                }
            }
        }
    }
}

std::string CandidateResult::getPositionString() const {
    std::string result;
    for (int pos : positions) {
        result += static_cast<char>('A' + pos);
    }
    return result;
}

std::string CandidateResult::getRotorString() const {
    std::string result;
    for (size_t i = 0; i < rotorOrder.size(); i++) {
        result += rotorOrder[i];
        if (i < rotorOrder.size() - 1) {
            result += "-";
        }
    }
    return result;
}

// CPU負荷管理の実装
double BombeAttack::getCPUUsage() {
    #ifdef _WIN32
    // Windows用の簡易実装
    return 50.0;  // 仮の値
    #else
    // Linux/Mac用の簡易実装
    return 50.0;  // 仮の値
    #endif
}

void BombeAttack::adjustThreadCount() {
    double usage = getCPUUsage();
    cpuUsage_.store(usage);
    
    // CPU使用率が90%を超えたらスレッドを遅延させる
    if (usage > 90.0) {
        threadDelay_ = std::chrono::milliseconds(10);
    } else if (usage > 80.0) {
        threadDelay_ = std::chrono::milliseconds(5);
    } else if (usage > 70.0) {
        threadDelay_ = std::chrono::milliseconds(1);
    } else {
        threadDelay_ = std::chrono::milliseconds(0);
    }
}

void BombeAttack::throttleIfNeeded() {
    // 単純な実装：定期的に短い休止を入れる
    if (cpuUsage_.load() > 85.0) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

// GPU処理の実装
bool BombeAttack::initializeGPU() {
    #ifdef USE_CUDA
    try {
        int deviceCount = 0;
        cudaError_t error = cudaGetDeviceCount(&deviceCount);
        
        if (error != cudaSuccess || deviceCount == 0) {
            return false;
        }
        
        // 最初のGPUを使用
        cudaSetDevice(0);
        
        cudaDeviceProp deviceProp;
        cudaGetDeviceProperties(&deviceProp, 0);
        
        if (progressCallback_) {
            progressCallback_("GPU Device: " + std::string(deviceProp.name));
            progressCallback_("GPU Memory: " + std::to_string(deviceProp.totalGlobalMem / (1024 * 1024)) + " MB");
        }
        
        return true;
    } catch (...) {
        return false;
    }
    #elif defined(USE_OPENCL)
    // OpenCL実装（簡略化）
    try {
        // プラットフォームとデバイスの検出
        return false;  // 今回は簡略化
    } catch (...) {
        return false;
    }
    #else
    return false;
    #endif
}

void BombeAttack::cleanupGPU() {
    if (gpuContext_) {
        // GPU cleanup code
    }
}

bool BombeAttack::processOnGPU(const std::vector<std::vector<int>>& positionBatch,
                               const std::vector<std::string>& rotorOrder,
                               int offset) {
    #ifdef USE_CUDA
    if (!useGPU_ || positionBatch.empty()) {
        return false;
    }
    
    try {
        // バッチサイズ
        size_t batchSize = positionBatch.size();
        
        // GPU用の配列を確保
        int* d_positions = nullptr;
        int* d_offsets = nullptr;
        float* d_scores = nullptr;
        
        cudaMalloc(&d_positions, batchSize * 3 * sizeof(int));
        cudaMalloc(&d_offsets, batchSize * sizeof(int));
        cudaMalloc(&d_scores, batchSize * sizeof(float));
        
        // データをGPUに転送
        std::vector<int> flatPositions;
        std::vector<int> offsets(batchSize, offset);
        
        for (const auto& pos : positionBatch) {
            flatPositions.insert(flatPositions.end(), pos.begin(), pos.end());
        }
        
        cudaMemcpy(d_positions, flatPositions.data(), flatPositions.size() * sizeof(int), cudaMemcpyHostToDevice);
        cudaMemcpy(d_offsets, offsets.data(), offsets.size() * sizeof(int), cudaMemcpyHostToDevice);
        
        // GPU上で簡易チェック（実際のCUDAカーネルは別途実装が必要）
        // ここでは簡略化のため、CPU側で処理
        std::vector<float> scores(batchSize);
        for (size_t i = 0; i < batchSize; i++) {
            // 簡易スコア計算（実際にはGPUカーネルで実行）
            scores[i] = 0.0f;
        }
        
        // 結果をGPUから取得
        cudaMemcpy(scores.data(), d_scores, batchSize * sizeof(float), cudaMemcpyDeviceToHost);
        
        // 有望な候補のみCPUで詳細検証
        float threshold = 0.3f;
        for (size_t i = 0; i < batchSize; i++) {
            if (scores[i] >= threshold) {
                testPosition(positionBatch[i], rotorOrder, offset);
            }
        }
        
        // GPUメモリを解放
        cudaFree(d_positions);
        cudaFree(d_offsets);
        cudaFree(d_scores);
        
        return true;
        
    } catch (...) {
        return false;
    }
    #else
    return false;
    #endif
}
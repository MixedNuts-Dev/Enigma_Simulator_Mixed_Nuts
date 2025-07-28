#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <memory>
#include <algorithm>
#include <nlohmann/json.hpp>

#include "core/Rotor.h"
#include "core/Reflector.h"
#include "core/Plugboard.h"
#include "core/EnigmaMachine.h"
#include "core/RotorConfig.h"

using json = nlohmann::json;

void printUsage() {
    std::cout << "Enigma Machine Simulator\n";
    std::cout << "Usage:\n";
    std::cout << "  1. encrypt - Encrypt/decrypt a message\n";
    std::cout << "  2. save - Save current configuration to JSON\n";
    std::cout << "  3. load - Load configuration from JSON\n";
    std::cout << "  4. bombe - Run Bombe attack (simplified)\n";
    std::cout << "  5. exit - Exit the program\n\n";
}

class EnigmaConsole {
private:
    std::unique_ptr<EnigmaMachine> enigma;
    std::string rotor1Type = "I";
    std::string rotor2Type = "II";
    std::string rotor3Type = "III";
    std::string reflectorType = "B";
    int rotor1Pos = 0;
    int rotor2Pos = 0;
    int rotor3Pos = 0;
    std::vector<std::string> plugboardPairs;

    void setupEnigma() {
        auto rotors = std::vector<std::unique_ptr<Rotor>>();
        
        // Create rotors based on configuration
        auto& r1Def = enigma::ROTOR_DEFINITIONS.at(rotor1Type);
        rotors.push_back(std::make_unique<Rotor>(r1Def.wiring, r1Def.getFirstNotch()));
        
        auto& r2Def = enigma::ROTOR_DEFINITIONS.at(rotor2Type);
        rotors.push_back(std::make_unique<Rotor>(r2Def.wiring, r2Def.getFirstNotch()));
        
        auto& r3Def = enigma::ROTOR_DEFINITIONS.at(rotor3Type);
        rotors.push_back(std::make_unique<Rotor>(r3Def.wiring, r3Def.getFirstNotch()));
        
        // Create reflector
        auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType);
        auto reflector = std::make_unique<Reflector>(refDef.wiring);
        
        // Create plugboard
        auto plugboard = std::make_unique<Plugboard>(plugboardPairs);
        
        // Create Enigma machine
        enigma = std::make_unique<EnigmaMachine>(
            std::move(rotors), 
            std::move(reflector), 
            std::move(plugboard)
        );
        
        // Set rotor positions
        enigma->setRotorPositions({rotor1Pos, rotor2Pos, rotor3Pos});
    }

public:
    EnigmaConsole() {
        setupEnigma();
    }

    void configure() {
        std::cout << "\n=== Configure Enigma Machine ===\n";
        
        // Rotor types
        std::cout << "Available rotors: I, II, III, IV, V, VI, VII, VIII\n";
        std::cout << "Enter rotor 1 type [" << rotor1Type << "]: ";
        std::string input;
        std::getline(std::cin, input);
        if (!input.empty()) rotor1Type = input;
        
        std::cout << "Enter rotor 2 type [" << rotor2Type << "]: ";
        std::getline(std::cin, input);
        if (!input.empty()) rotor2Type = input;
        
        std::cout << "Enter rotor 3 type [" << rotor3Type << "]: ";
        std::getline(std::cin, input);
        if (!input.empty()) rotor3Type = input;
        
        // Reflector
        std::cout << "Available reflectors: B, C\n";
        std::cout << "Enter reflector type [" << reflectorType << "]: ";
        std::getline(std::cin, input);
        if (!input.empty()) reflectorType = input;
        
        // Rotor positions
        std::cout << "Enter rotor positions (A-Z):\n";
        std::cout << "Rotor 1 position [" << char('A' + rotor1Pos) << "]: ";
        std::getline(std::cin, input);
        if (!input.empty() && input[0] >= 'A' && input[0] <= 'Z') {
            rotor1Pos = input[0] - 'A';
        }
        
        std::cout << "Rotor 2 position [" << char('A' + rotor2Pos) << "]: ";
        std::getline(std::cin, input);
        if (!input.empty() && input[0] >= 'A' && input[0] <= 'Z') {
            rotor2Pos = input[0] - 'A';
        }
        
        std::cout << "Rotor 3 position [" << char('A' + rotor3Pos) << "]: ";
        std::getline(std::cin, input);
        if (!input.empty() && input[0] >= 'A' && input[0] <= 'Z') {
            rotor3Pos = input[0] - 'A';
        }
        
        // Plugboard
        std::cout << "Enter plugboard pairs (e.g., AB CD EF) [" << getPlugboardString() << "]: ";
        std::getline(std::cin, input);
        if (!input.empty()) {
            plugboardPairs.clear();
            std::istringstream iss(input);
            std::string pair;
            while (iss >> pair) {
                if (pair.length() == 2) {
                    plugboardPairs.push_back(pair);
                }
            }
        }
        
        setupEnigma();
        std::cout << "Configuration updated.\n";
    }

    void encrypt() {
        std::cout << "\n=== Encrypt/Decrypt Message ===\n";
        std::cout << "Current configuration:\n";
        std::cout << "  Rotors: " << rotor1Type << "-" << rotor2Type << "-" << rotor3Type << "\n";
        std::cout << "  Positions: " << char('A' + rotor1Pos) << char('A' + rotor2Pos) << char('A' + rotor3Pos) << "\n";
        std::cout << "  Reflector: " << reflectorType << "\n";
        std::cout << "  Plugboard: " << getPlugboardString() << "\n\n";
        
        std::cout << "Enter message: ";
        std::string message;
        std::getline(std::cin, message);
        
        // Reset rotor positions before encryption
        enigma->setRotorPositions({rotor1Pos, rotor2Pos, rotor3Pos});
        
        std::string result = enigma->encrypt(message);
        std::cout << "Result: " << result << "\n";
    }

    void saveConfig() {
        std::cout << "Enter filename to save configuration: ";
        std::string filename;
        std::getline(std::cin, filename);
        
        json config;
        config["rotors"]["types"] = {rotor1Type, rotor2Type, rotor3Type};
        config["rotors"]["positions"] = {
            std::string(1, char('A' + rotor1Pos)),
            std::string(1, char('A' + rotor2Pos)),
            std::string(1, char('A' + rotor3Pos))
        };
        config["reflector"] = reflectorType;
        config["plugboard"] = getPlugboardString();
        
        std::ofstream file(filename);
        if (file.is_open()) {
            file << config.dump(2);
            file.close();
            std::cout << "Configuration saved to " << filename << "\n";
        } else {
            std::cout << "Error: Could not save file.\n";
        }
    }

    void loadConfig() {
        std::cout << "Enter filename to load configuration: ";
        std::string filename;
        std::getline(std::cin, filename);
        
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cout << "Error: Could not open file.\n";
            return;
        }
        
        try {
            json config;
            file >> config;
            
            // Load rotor types
            if (config.contains("rotors") && config["rotors"].contains("types")) {
                auto types = config["rotors"]["types"];
                if (types.size() >= 3) {
                    rotor1Type = types[0];
                    rotor2Type = types[1];
                    rotor3Type = types[2];
                }
            }
            
            // Load rotor positions
            if (config.contains("rotors") && config["rotors"].contains("positions")) {
                auto positions = config["rotors"]["positions"];
                if (positions.size() >= 3) {
                    std::string pos1 = positions[0];
                    std::string pos2 = positions[1];
                    std::string pos3 = positions[2];
                    
                    if (!pos1.empty()) rotor1Pos = pos1[0] - 'A';
                    if (!pos2.empty()) rotor2Pos = pos2[0] - 'A';
                    if (!pos3.empty()) rotor3Pos = pos3[0] - 'A';
                }
            }
            
            // Load reflector
            if (config.contains("reflector")) {
                reflectorType = config["reflector"];
            }
            
            // Load plugboard
            if (config.contains("plugboard")) {
                std::string pb = config["plugboard"];
                plugboardPairs.clear();
                std::istringstream iss(pb);
                std::string pair;
                while (iss >> pair) {
                    if (pair.length() == 2) {
                        plugboardPairs.push_back(pair);
                    }
                }
            }
            
            setupEnigma();
            std::cout << "Configuration loaded from " << filename << "\n";
            
        } catch (const std::exception& e) {
            std::cout << "Error loading configuration: " << e.what() << "\n";
        }
    }

    void loadBombeResult() {
        std::cout << "Enter Bombe result JSON filename: ";
        std::string filename;
        std::getline(std::cin, filename);
        
        std::ifstream file(filename);
        if (!file.is_open()) {
            std::cout << "Error: Could not open file.\n";
            return;
        }
        
        try {
            json bombeResult;
            file >> bombeResult;
            
            if (!bombeResult.contains("results") || !bombeResult.contains("settings")) {
                std::cout << "Error: This is not a valid Bombe result file.\n";
                return;
            }
            
            auto results = bombeResult["results"];
            if (results.empty()) {
                std::cout << "No results found in file.\n";
                return;
            }
            
            // Show top results
            std::cout << "\nTop Bombe results:\n";
            for (size_t i = 0; i < std::min(size_t(10), results.size()); ++i) {
                auto result = results[i];
                std::cout << i + 1 << ". Position: " << result["position"]
                         << " Rotors: " << result["rotors"]
                         << " Score: " << result["score"]
                         << " Match: " << result["matchRate"] << "\n";
            }
            
            std::cout << "\nSelect result number to apply (1-" << std::min(size_t(10), results.size()) << "): ";
            std::string input;
            std::getline(std::cin, input);
            
            int selection = std::stoi(input) - 1;
            if (selection >= 0 && selection < results.size()) {
                auto selected = results[selection];
                
                // Apply rotor configuration
                std::string rotorConfig = selected["rotors"];
                size_t pos1 = rotorConfig.find('-');
                size_t pos2 = rotorConfig.find('-', pos1 + 1);
                
                if (pos1 != std::string::npos && pos2 != std::string::npos) {
                    rotor1Type = rotorConfig.substr(0, pos1);
                    rotor2Type = rotorConfig.substr(pos1 + 1, pos2 - pos1 - 1);
                    rotor3Type = rotorConfig.substr(pos2 + 1);
                }
                
                // Apply positions
                std::string positions = selected["position"];
                if (positions.length() >= 3) {
                    rotor1Pos = positions[0] - 'A';
                    rotor2Pos = positions[1] - 'A';
                    rotor3Pos = positions[2] - 'A';
                }
                
                // Apply reflector from settings
                if (bombeResult["settings"].contains("reflector")) {
                    reflectorType = bombeResult["settings"]["reflector"];
                }
                
                // Apply plugboard
                plugboardPairs.clear();
                if (selected.contains("plugboard")) {
                    for (const auto& pair : selected["plugboard"]) {
                        plugboardPairs.push_back(pair);
                    }
                }
                
                setupEnigma();
                std::cout << "Bombe result applied successfully.\n";
            }
            
        } catch (const std::exception& e) {
            std::cout << "Error loading Bombe result: " << e.what() << "\n";
        }
    }

private:
    std::string getPlugboardString() const {
        std::string result;
        for (const auto& pair : plugboardPairs) {
            if (!result.empty()) result += " ";
            result += pair;
        }
        return result;
    }
};

int main() {
    std::cout << "=== Enigma Machine Simulator (C++ Version) ===\n\n";
    
    EnigmaConsole console;
    
    while (true) {
        printUsage();
        std::cout << "Enter command: ";
        std::string command;
        std::getline(std::cin, command);
        
        if (command == "1" || command == "encrypt") {
            console.encrypt();
        } else if (command == "2" || command == "save") {
            console.saveConfig();
        } else if (command == "3" || command == "load") {
            console.loadConfig();
        } else if (command == "4" || command == "bombe") {
            console.loadBombeResult();
        } else if (command == "5" || command == "exit") {
            break;
        } else if (command == "config") {
            console.configure();
        } else {
            std::cout << "Unknown command. Please try again.\n";
        }
        
        std::cout << "\n";
    }
    
    return 0;
}
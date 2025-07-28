#ifndef ENIGMA_MACHINE_H
#define ENIGMA_MACHINE_H

#include <vector>
#include <memory>
#include <string>
#include "Rotor.h"
#include "Reflector.h"
#include "Plugboard.h"

class EnigmaMachine {
public:
    EnigmaMachine(std::vector<std::unique_ptr<Rotor>> rotors,
                  std::unique_ptr<Reflector> reflector,
                  std::unique_ptr<Plugboard> plugboard);
    
    void setRotorPositions(const std::vector<int>& positions);
    std::string encrypt(const std::string& message);
    
    // For fast Bombe attack
    char encryptChar(char c);
    void stepRotors();
    void resetToPosition(const std::vector<int>& positions);
    
    // Get current rotor positions
    std::vector<int> getRotorPositions() const;
    
private:
    std::vector<std::unique_ptr<Rotor>> rotors_;
    std::unique_ptr<Reflector> reflector_;
    std::unique_ptr<Plugboard> plugboard_;
    
    void stepRotorsInternal();
};

#endif // ENIGMA_MACHINE_H
#include "EnigmaMachine.h"
#include <algorithm>

EnigmaMachine::EnigmaMachine(std::vector<std::unique_ptr<Rotor>> rotors,
                             std::unique_ptr<Reflector> reflector,
                             std::unique_ptr<Plugboard> plugboard)
    : rotors_(std::move(rotors)),
      reflector_(std::move(reflector)),
      plugboard_(std::move(plugboard)) {
}

void EnigmaMachine::setRotorPositions(const std::vector<int>& positions) {
    for (size_t i = 0; i < std::min(positions.size(), rotors_.size()); ++i) {
        rotors_[i]->setPosition(positions[i]);
    }
}

std::string EnigmaMachine::encrypt(const std::string& message) {
    std::string result;
    
    for (char c : message) {
        if (c >= 'A' && c <= 'Z') {
            result += encryptChar(c);
        } else if (c >= 'a' && c <= 'z') {
            result += encryptChar(c - 'a' + 'A');
        }
    }
    
    return result;
}

char EnigmaMachine::encryptChar(char c) {
    // Step rotors before encryption
    stepRotors();
    
    // Pass through plugboard
    c = plugboard_->swap(c);
    
    // Pass through rotors (right to left)
    for (const auto& rotor : rotors_) {
        c = rotor->encryptForward(c);
    }
    
    // Pass through reflector
    c = reflector_->reflect(c);
    
    // Pass back through rotors (left to right)
    for (auto it = rotors_.rbegin(); it != rotors_.rend(); ++it) {
        c = (*it)->encryptBackward(c);
    }
    
    // Pass through plugboard again
    c = plugboard_->swap(c);
    
    return c;
}

void EnigmaMachine::stepRotors() {
    // Enigma double-stepping mechanism
    bool middleAtNotch = false;
    if (rotors_.size() >= 2) {
        middleAtNotch = rotors_[1]->isAtNotch();
    }
    
    // Always rotate the rightmost rotor
    if (!rotors_.empty()) {
        rotors_[0]->rotate();
    }
    
    // Check for middle rotor step
    if (rotors_.size() >= 2) {
        if (rotors_[0]->isAtNotch() || middleAtNotch) {
            rotors_[1]->rotate();
            
            // Check for left rotor step
            if (rotors_.size() >= 3 && middleAtNotch) {
                rotors_[2]->rotate();
            }
        }
    }
}

void EnigmaMachine::resetToPosition(const std::vector<int>& positions) {
    setRotorPositions(positions);
}

std::vector<int> EnigmaMachine::getRotorPositions() const {
    std::vector<int> positions;
    for (const auto& rotor : rotors_) {
        positions.push_back(rotor->getPosition());
    }
    return positions;
}
#include "Rotor.h"
#include <algorithm>

Rotor::Rotor(const std::string& mapping, int notch, int ringSetting)
    : originalMapping_(mapping), position_(0), notch_(notch), ringSetting_(ringSetting) {
    updateMappings();
}

void Rotor::setPosition(int position) {
    position_ = mod26(position);
}

void Rotor::setRing(int ringSetting) {
    ringSetting_ = mod26(ringSetting);
    updateMappings();
}

void Rotor::rotate() {
    position_ = mod26(position_ + 1);
}

bool Rotor::isAtNotch() const {
    return position_ == notch_;
}

void Rotor::updateMappings() {
    // Pre-compute forward and backward mappings for efficiency
    for (int i = 0; i < 26; ++i) {
        forwardMapping_[i] = originalMapping_[i];
        backwardMapping_[originalMapping_[i] - 'A'] = 'A' + i;
    }
}

char Rotor::encryptForward(char c) const {
    int idx = c - 'A';
    idx = mod26(idx + position_ - ringSetting_);
    char encrypted = forwardMapping_[idx];
    int encryptedIdx = encrypted - 'A';
    encryptedIdx = mod26(encryptedIdx - position_ + ringSetting_);
    return 'A' + encryptedIdx;
}

char Rotor::encryptBackward(char c) const {
    int idx = c - 'A';
    idx = mod26(idx + position_ - ringSetting_);
    int decryptedIdx = backwardMapping_[idx] - 'A';
    decryptedIdx = mod26(decryptedIdx - position_ + ringSetting_);
    return 'A' + decryptedIdx;
}
#include "Reflector.h"

Reflector::Reflector(const std::string& wiring) : wiring_(wiring) {}

char Reflector::reflect(char c) const {
    int index = c - 'A';
    return wiring_[index];
}
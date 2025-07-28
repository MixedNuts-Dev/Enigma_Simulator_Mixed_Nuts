#ifndef ROTOR_CONFIG_H
#define ROTOR_CONFIG_H

#include <string>
#include <unordered_map>
#include <vector>

namespace enigma {

struct RotorDefinition {
    std::string wiring;
    std::vector<int> notches;
    
    int getFirstNotch() const {
        return notches.empty() ? 0 : notches[0];
    }
};

struct ReflectorDefinition {
    std::string wiring;
};

const std::unordered_map<std::string, RotorDefinition> ROTOR_DEFINITIONS = {
    {"I",    {"EKMFLGDQVZNTOWYHXUSPAIBRCJ", {16}}},  // Q
    {"II",   {"AJDKSIRUXBLHWTMCQGZNPYFVOE", {4}}},   // E
    {"III",  {"BDFHJLCPRTXVZNYEIWGAKMUSQO", {21}}},  // V
    {"IV",   {"ESOVPZJAYQUIRHXLNFTGKDCMWB", {9}}},   // J
    {"V",    {"VZBRGITYUPSDNHLXAWMJQOFECK", {25}}},  // Z
    {"VI",   {"JPGVOUMFYQBENHZRDKASXLICTW", {25, 12}}}, // Z and M
    {"VII",  {"NZJHGRCXMYSWBOUFAIVLPEKQDT", {25, 12}}}, // Z and M
    {"VIII", {"FKQHTLXOCBJSPDZRAMEWNIUYGV", {25, 12}}}  // Z and M
};

const std::unordered_map<std::string, ReflectorDefinition> REFLECTOR_DEFINITIONS = {
    {"B", {"YRUHQSLDPXNGOKMIEBFZCWVJAT"}},
    {"C", {"FVPJIAOYEDRZXWGCTKUQSBNMHL"}}
};

} // namespace enigma

#endif // ROTOR_CONFIG_H
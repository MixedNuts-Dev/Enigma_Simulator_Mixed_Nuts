#ifndef ROTOR_H
#define ROTOR_H

#include <string>
#include <array>

class Rotor {
public:
    Rotor(const std::string& mapping, int notch, int ringSetting = 0);
    
    void setPosition(int position);
    void setRing(int ringSetting);
    void rotate();
    bool isAtNotch() const;
    
    char encryptForward(char c) const;
    char encryptBackward(char c) const;
    
    int getPosition() const { return position_; }
    
private:
    static constexpr const char* ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    
    std::string originalMapping_;
    std::array<char, 26> forwardMapping_;
    std::array<char, 26> backwardMapping_;
    int position_;
    int notch_;
    int ringSetting_;
    
    void updateMappings();
    inline int mod26(int x) const { return ((x % 26) + 26) % 26; }
};

#endif // ROTOR_H
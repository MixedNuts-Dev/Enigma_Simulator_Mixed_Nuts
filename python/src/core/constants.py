"""Constants and configurations for Enigma machine."""

# Rotor configurations
ROTOR_DEFINITIONS = {
    "I": {"wiring": "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "notch": 16},  # ノッチ at Q
    "II": {"wiring": "AJDKSIRUXBLHWTMCQGZNPYFVOE", "notch": 4},   # ノッチ at E
    "III": {"wiring": "BDFHJLCPRTXVZNYEIWGAKMUSQO", "notch": 21}, # ノッチ at V
    "IV": {"wiring": "ESOVPZJAYQUIRHXLNFTGKDCMWB", "notch": 9},   # ノッチ at J
    "V": {"wiring": "VZBRGITYUPSDNHLXAWMJQOFECK", "notch": 25},   # ノッチ at Z
    "VI": {"wiring": "JPGVOUMFYQBENHZRDKASXLICTW", "notches": [12, 25]},  # ノッチ at M, Z
    "VII": {"wiring": "NZJHGRCXMYSWBOUFAIVLPEKQDT", "notches": [12, 25]},  # ノッチ at M, Z
    "VIII": {"wiring": "FKQHTLXOCBJSPDZRAMEWNIUYGV", "notches": [12, 25]},  # ノッチ at M, Z
}

# Reflector configurations
REFLECTOR_DEFINITIONS = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
}
"""エニグママシンの定数と設定"""

# ローター設定
ROTOR_DEFINITIONS = {
    "I": {"wiring": "EKMFLGDQVZNTOWYHXUSPAIBRCJ", "notch": 16},  # ノッチ位置: Q
    "II": {"wiring": "AJDKSIRUXBLHWTMCQGZNPYFVOE", "notch": 4},   # ノッチ位置: E
    "III": {"wiring": "BDFHJLCPRTXVZNYEIWGAKMUSQO", "notch": 21}, # ノッチ位置: V
    "IV": {"wiring": "ESOVPZJAYQUIRHXLNFTGKDCMWB", "notch": 9},   # ノッチ位置: J
    "V": {"wiring": "VZBRGITYUPSDNHLXAWMJQOFECK", "notch": 25},   # ノッチ位置: Z
    "VI": {"wiring": "JPGVOUMFYQBENHZRDKASXLICTW", "notches": [12, 25]},  # ノッチ位置: M, Z
    "VII": {"wiring": "NZJHGRCXMYSWBOUFAIVLPEKQDT", "notches": [12, 25]},  # ノッチ位置: M, Z
    "VIII": {"wiring": "FKQHTLXOCBJSPDZRAMEWNIUYGV", "notches": [12, 25]},  # ノッチ位置: M, Z
}

# リフレクター設定
REFLECTOR_DEFINITIONS = {
    "B": "YRUHQSLDPXNGOKMIEBFZCWVJAT",
    "C": "FVPJIAOYEDRZXWGCTKUQSBNMHL",
}
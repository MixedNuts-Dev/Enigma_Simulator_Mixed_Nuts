package com.enigma.core;

import java.util.HashMap;
import java.util.Map;

public class RotorConfig {
    public static final Map<String, RotorDefinition> ROTOR_DEFINITIONS = new HashMap<>();
    public static final Map<String, String> REFLECTOR_DEFINITIONS = new HashMap<>();
    
    static {
        // Historical rotor wirings and notch positions
        ROTOR_DEFINITIONS.put("I", new RotorDefinition("EKMFLGDQVZNTOWYHXUSPAIBRCJ", 16)); // Notch at Q
        ROTOR_DEFINITIONS.put("II", new RotorDefinition("AJDKSIRUXBLHWTMCQGZNPYFVOE", 4));  // Notch at E
        ROTOR_DEFINITIONS.put("III", new RotorDefinition("BDFHJLCPRTXVZNYEIWGAKMUSQO", 21)); // Notch at V
        ROTOR_DEFINITIONS.put("IV", new RotorDefinition("ESOVPZJAYQUIRHXLNFTGKDCMWB", 9));  // Notch at J
        ROTOR_DEFINITIONS.put("V", new RotorDefinition("VZBRGITYUPSDNHLXAWMJQOFECK", 25));  // Notch at Z
        ROTOR_DEFINITIONS.put("VI", new RotorDefinition("JPGVOUMFYQBENHZRDKASXLICTW", new int[]{12, 25})); // Notches at M, Z
        ROTOR_DEFINITIONS.put("VII", new RotorDefinition("NZJHGRCXMYSWBOUFAIVLPEKQDT", new int[]{12, 25})); // Notches at M, Z
        ROTOR_DEFINITIONS.put("VIII", new RotorDefinition("FKQHTLXOCBJSPDZRAMEWNIUYGV", new int[]{12, 25})); // Notches at M, Z
        
        // Reflector wirings
        REFLECTOR_DEFINITIONS.put("B", "YRUHQSLDPXNGOKMIEBFZCWVJAT");
        REFLECTOR_DEFINITIONS.put("C", "FVPJIAOYEDRZXWGCTKUQSBNMHL");
    }
    
    public static class RotorDefinition {
        public final String wiring;
        public final int[] notches;
        
        public RotorDefinition(String wiring, int notch) {
            this.wiring = wiring;
            this.notches = new int[]{notch};
        }
        
        public RotorDefinition(String wiring, int[] notches) {
            this.wiring = wiring;
            this.notches = notches;
        }
        
        public int getFirstNotch() {
            return notches[0];
        }
    }
}
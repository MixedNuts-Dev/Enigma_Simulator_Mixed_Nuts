package com.enigma.core;

import java.util.List;

public class EnigmaMachine {
    private final List<Rotor> rotors;
    private final Reflector reflector;
    private Plugboard plugboard;
    
    public EnigmaMachine(List<Rotor> rotors, Reflector reflector, Plugboard plugboard) {
        this.rotors = rotors;
        this.reflector = reflector;
        this.plugboard = plugboard;
    }
    
    public void setRotorPositions(int[] positions) {
        for (int i = 0; i < rotors.size() && i < positions.length; i++) {
            rotors.get(i).setPosition(positions[i]);
        }
    }
    
    public void setPlugboard(Plugboard plugboard) {
        this.plugboard = plugboard;
    }
    
    public String encrypt(String message) {
        StringBuilder encrypted = new StringBuilder();
        
        for (char c : message.toUpperCase().toCharArray()) {
            if (Character.isLetter(c)) {
                // Step rotors before encrypting
                stepRotors();
                
                // Encryption process
                char encryptedChar = plugboard.swap(c);
                
                // Forward through rotors
                for (Rotor rotor : rotors) {
                    encryptedChar = rotor.encryptForward(encryptedChar);
                }
                
                // Reflect
                encryptedChar = reflector.reflect(encryptedChar);
                
                // Backward through rotors
                for (int i = rotors.size() - 1; i >= 0; i--) {
                    encryptedChar = rotors.get(i).encryptBackward(encryptedChar);
                }
                
                // Final plugboard swap
                encryptedChar = plugboard.swap(encryptedChar);
                encrypted.append(encryptedChar);
            }
        }
        
        return encrypted.toString();
    }
    
    private void stepRotors() {
        // Double stepping mechanism
        boolean middleAtNotch = rotors.size() > 1 && rotors.get(1).isAtNotch();
        boolean rightAtNotch = rotors.get(0).isAtNotch();
        
        // Middle rotor double step
        if (middleAtNotch) {
            rotors.get(1).rotate();
            if (rotors.size() > 2) {
                rotors.get(2).rotate();
            }
        }
        // Normal stepping
        else if (rightAtNotch && rotors.size() > 1) {
            rotors.get(1).rotate();
        }
        
        // Right rotor always rotates
        rotors.get(0).rotate();
    }
    
    public List<Rotor> getRotors() {
        return rotors;
    }
    
    public int[] getRotorPositions() {
        int[] positions = new int[rotors.size()];
        for (int i = 0; i < rotors.size(); i++) {
            positions[i] = rotors.get(i).getPosition();
        }
        return positions;
    }
}
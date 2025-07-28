package com.enigma.core;

public class Rotor {
    private final String originalMapping;
    private String mapping;
    private int position;
    private final int notch;
    private int ringSetting;
    
    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    
    public Rotor(String mapping, int notch) {
        this(mapping, notch, 0);
    }
    
    public Rotor(String mapping, int notch, int ringSetting) {
        this.originalMapping = mapping;
        this.mapping = mapping;
        this.position = 0;
        this.notch = notch;
        this.ringSetting = ringSetting;
    }
    
    public void setPosition(int position) {
        this.position = position;
        this.mapping = originalMapping;
    }
    
    public void setRing(int ringSetting) {
        this.ringSetting = ringSetting % 26;
    }
    
    public void rotate() {
        position = (position + 1) % 26;
    }
    
    public boolean isAtNotch() {
        return position == notch;
    }
    
    public char encryptForward(char c) {
        int idx = ALPHABET.indexOf(c);
        idx = (idx + position - ringSetting + 26) % 26;
        char encrypted = mapping.charAt(idx);
        int encryptedIdx = ALPHABET.indexOf(encrypted);
        encryptedIdx = (encryptedIdx - position + ringSetting + 26) % 26;
        return ALPHABET.charAt(encryptedIdx);
    }
    
    public char encryptBackward(char c) {
        int idx = ALPHABET.indexOf(c);
        idx = (idx + position - ringSetting + 26) % 26;
        int decryptedIdx = mapping.indexOf(ALPHABET.charAt(idx));
        decryptedIdx = (decryptedIdx - position + ringSetting + 26) % 26;
        return ALPHABET.charAt(decryptedIdx);
    }
    
    public int getPosition() {
        return position;
    }
}
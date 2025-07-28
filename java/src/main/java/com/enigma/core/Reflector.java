package com.enigma.core;

public class Reflector {
    private final String mapping;
    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    
    public Reflector(String mapping) {
        this.mapping = mapping;
    }
    
    public char reflect(char c) {
        return mapping.charAt(ALPHABET.indexOf(c));
    }
}
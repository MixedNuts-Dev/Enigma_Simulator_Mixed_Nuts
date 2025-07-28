package com.enigma.core;

import java.util.HashMap;
import java.util.Map;

public class Plugboard {
    private final Map<Character, Character> mapping;
    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    
    public Plugboard(String[] swaps) {
        mapping = new HashMap<>();
        
        // Initialize identity mapping
        for (char c : ALPHABET.toCharArray()) {
            mapping.put(c, c);
        }
        
        // Apply swaps
        if (swaps != null && !(swaps.length == 1 && swaps[0].equals("00"))) {
            for (String swap : swaps) {
                if (swap.length() == 2) {
                    char a = swap.charAt(0);
                    char b = swap.charAt(1);
                    mapping.put(a, b);
                    mapping.put(b, a);
                }
            }
        }
    }
    
    public char swap(char c) {
        return mapping.getOrDefault(c, c);
    }
}
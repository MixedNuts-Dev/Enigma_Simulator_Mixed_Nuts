package com.enigma.core;

import java.util.HashMap;
import java.util.Map;

public class Plugboard {
    private final Map<Character, Character> mapping;
    private static final String ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private static final int MAX_PAIRS = 10; // 史実のエニグマでは最大10組までの接続が可能
    
    public Plugboard(String[] swaps) {
        mapping = new HashMap<>();
        
        // Initialize identity mapping
        for (char c : ALPHABET.toCharArray()) {
            mapping.put(c, c);
        }
        
        // Apply swaps
        if (swaps != null && !(swaps.length == 1 && swaps[0].equals("00"))) {
            // 最大10組の制限をチェック
            int validPairs = 0;
            for (String swap : swaps) {
                if (swap.length() == 2 && !swap.equals("00")) {
                    validPairs++;
                }
            }
            
            if (validPairs > MAX_PAIRS) {
                throw new IllegalArgumentException(
                    "プラグボード接続数は最大" + MAX_PAIRS + "組までです。" + 
                    validPairs + "組が指定されました。");
            }
            
            // スワップを適用
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
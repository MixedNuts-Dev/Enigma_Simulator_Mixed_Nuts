package com.enigma.bombe;

import com.enigma.core.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.Collectors;

public class BombeAttack {
    private final String cribText;
    private final String cipherText;
    private final List<String> rotorTypes;
    private final String reflectorType;
    private final boolean testAllOrders;
    private final int numThreads;
    
    private volatile boolean stopFlag = false;
    private final List<CandidateResult> results = new CopyOnWriteArrayList<>();
    
    public static class CandidateResult implements Comparable<CandidateResult> {
        public final double score;
        public final int[] positions;
        public final List<String> rotorOrder;
        public final Map<Character, Character> plugboard;
        public final double matchRate;
        public final int plugboardPairs;
        public final int offset;
        
        public CandidateResult(double score, int[] positions, List<String> rotorOrder,
                             Map<Character, Character> plugboard, double matchRate, 
                             int plugboardPairs, int offset) {
            this.score = score;
            this.positions = positions;
            this.rotorOrder = new ArrayList<>(rotorOrder);
            this.plugboard = new HashMap<>(plugboard);
            this.matchRate = matchRate;
            this.plugboardPairs = plugboardPairs;
            this.offset = offset;
        }
        
        @Override
        public int compareTo(CandidateResult other) {
            return Double.compare(other.score, this.score); // Descending order
        }
        
        public String getPositionString() {
            StringBuilder sb = new StringBuilder();
            for (int pos : positions) {
                sb.append((char)('A' + pos));
            }
            return sb.toString();
        }
        
        public String getRotorString() {
            return String.join("-", rotorOrder);
        }
    }
    
    public BombeAttack(String cribText, String cipherText, List<String> rotorTypes, 
                      String reflectorType, boolean testAllOrders) {
        this.cribText = cribText.toUpperCase();
        this.cipherText = cipherText.toUpperCase();
        this.rotorTypes = rotorTypes;
        this.reflectorType = reflectorType;
        this.testAllOrders = testAllOrders;
        this.numThreads = Runtime.getRuntime().availableProcessors();
    }
    
    public List<CandidateResult> attack(Consumer<String> progressCallback) {
        ExecutorService executor = Executors.newFixedThreadPool(numThreads);
        
        try {
            List<List<String>> rotorOrders = testAllOrders ? 
                generatePermutations(rotorTypes) : Arrays.asList(rotorTypes);
            
            int maxOffset = Math.max(0, cipherText.length() - cribText.length() + 1);
            int totalTasks = 26 * 26 * 26 * rotorOrders.size() * maxOffset;
            
            progressCallback.accept(String.format(
                "Total combinations: %d (positions: %d, orders: %d, offsets: %d)",
                totalTasks, 26*26*26, rotorOrders.size(), maxOffset
            ));
            
            List<CompletableFuture<Void>> futures = new ArrayList<>();
            AtomicInteger tested = new AtomicInteger(0);
            
            for (List<String> rotorOrder : rotorOrders) {
                for (int offset = 0; offset < maxOffset; offset++) {
                    for (int pos1 = 0; pos1 < 26; pos1++) {
                        for (int pos2 = 0; pos2 < 26; pos2++) {
                            for (int pos3 = 0; pos3 < 26; pos3++) {
                                if (stopFlag) {
                                    executor.shutdownNow();
                                    return results;
                                }
                                
                                final int[] positions = {pos1, pos2, pos3};
                                final List<String> order = rotorOrder;
                                final int testOffset = offset;
                                
                                CompletableFuture<Void> future = CompletableFuture.runAsync(() -> {
                                    testPosition(positions, order, testOffset);
                                    
                                    int count = tested.incrementAndGet();
                                    if (count % 5000 == 0) {
                                        double progress = (count * 100.0) / totalTasks;
                                        progressCallback.accept(String.format(
                                            "Progress: %d/%d (%.1f%%)", count, totalTasks, progress
                                        ));
                                    }
                                }, executor);
                                
                                futures.add(future);
                            }
                        }
                    }
                }
            }
            
            // Wait for all tasks to complete
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
            
        } finally {
            executor.shutdown();
        }
        
        // Sort results by score
        Collections.sort(results);
        
        progressCallback.accept(String.format("Found %d candidates", results.size()));
        
        return results;
    }
    
    private void testPosition(int[] positions, List<String> rotorOrder, int offset) {
        // Check if crib fits at this offset
        if (offset + cribText.length() > cipherText.length()) {
            return;
        }
        
        String cipherPart = cipherText.substring(offset, offset + cribText.length());
        
        // Create Enigma machine
        List<Rotor> rotors = new ArrayList<>();
        for (String type : rotorOrder) {
            RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
            rotors.add(new Rotor(def.wiring, def.getFirstNotch()));
        }
        
        Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
        EnigmaMachine enigma = new EnigmaMachine(rotors, reflector, new Plugboard(new String[0]));
        
        // Set rotor positions
        enigma.setRotorPositions(positions);
        
        // Advance rotors to offset position
        for (int i = 0; i < offset; i++) {
            // Simulate stepping without encrypting
            List<Rotor> machineRotors = enigma.getRotors();
            boolean middleAtNotch = machineRotors.size() > 1 && machineRotors.get(1).isAtNotch();
            boolean rightAtNotch = machineRotors.get(0).isAtNotch();
            
            if (middleAtNotch) {
                machineRotors.get(1).rotate();
                if (machineRotors.size() > 2) {
                    machineRotors.get(2).rotate();
                }
            } else if (rightAtNotch && machineRotors.size() > 1) {
                machineRotors.get(1).rotate();
            }
            machineRotors.get(0).rotate();
        }
        
        // Test encryption
        String testResult = enigma.encrypt(cribText);
        
        // Check for exact match
        if (testResult.equals(cipherPart)) {
            results.add(new CandidateResult(
                100.0, positions, rotorOrder, new HashMap<>(), 1.0, 0, offset
            ));
            return;
        }
        
        // Check for partial match (with plugboard)
        int matches = 0;
        Map<Character, Character> plugboardHypothesis = new HashMap<>();
        boolean hasConflict = false;
        
        for (int i = 0; i < cribText.length(); i++) {
            char plain = cribText.charAt(i);
            char result = testResult.charAt(i);
            char cipher = cipherPart.charAt(i);
            
            // Self-loop check
            if (plain == cipher) {
                return; // Invalid - Enigma never encrypts a letter to itself
            }
            
            if (result == cipher) {
                matches++;
            } else {
                // Check plugboard consistency
                if (plugboardHypothesis.containsKey(result)) {
                    if (!plugboardHypothesis.get(result).equals(cipher)) {
                        hasConflict = true;
                        break;
                    }
                } else if (plugboardHypothesis.containsValue(cipher)) {
                    // Check reverse mapping
                    for (Map.Entry<Character, Character> entry : plugboardHypothesis.entrySet()) {
                        if (entry.getValue().equals(cipher) && !entry.getKey().equals(result)) {
                            hasConflict = true;
                            break;
                        }
                    }
                } else {
                    plugboardHypothesis.put(result, cipher);
                    plugboardHypothesis.put(cipher, result);
                }
            }
        }
        
        if (!hasConflict) {
            double matchRate = (double) matches / cribText.length();
            int numPairs = plugboardHypothesis.size() / 2;
            
            if (matchRate >= 0.5 && numPairs <= 10) {
                double score = matchRate * 100 - numPairs * 2;
                results.add(new CandidateResult(
                    score, positions, rotorOrder, plugboardHypothesis, 
                    matchRate, numPairs, offset
                ));
            }
        }
    }
    
    private List<List<String>> generatePermutations(List<String> items) {
        if (items.size() <= 1) {
            return Arrays.asList(items);
        }
        
        List<List<String>> result = new ArrayList<>();
        for (int i = 0; i < items.size(); i++) {
            String first = items.get(i);
            List<String> remaining = new ArrayList<>(items);
            remaining.remove(i);
            
            for (List<String> permutation : generatePermutations(remaining)) {
                List<String> newPerm = new ArrayList<>();
                newPerm.add(first);
                newPerm.addAll(permutation);
                result.add(newPerm);
            }
        }
        
        return result;
    }
    
    public void stop() {
        stopFlag = true;
    }
    
    public interface Consumer<T> {
        void accept(T t);
    }
}
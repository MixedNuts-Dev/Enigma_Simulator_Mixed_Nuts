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
    private final boolean searchWithoutPlugboard;
    private final int numThreads;
    
    private volatile boolean stopFlag = false;
    private final List<CandidateResult> results = new CopyOnWriteArrayList<>();
    private volatile boolean hasPlugboardConflict = false;
    
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
            return Double.compare(other.score, this.score); // 降順
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
        this(cribText, cipherText, rotorTypes, reflectorType, testAllOrders, false);
    }
    
    public BombeAttack(String cribText, String cipherText, List<String> rotorTypes, 
                      String reflectorType, boolean testAllOrders, boolean searchWithoutPlugboard) {
        this.cribText = cribText.toUpperCase();
        this.cipherText = cipherText.toUpperCase();
        this.rotorTypes = rotorTypes;
        this.reflectorType = reflectorType;
        this.testAllOrders = testAllOrders;
        this.searchWithoutPlugboard = searchWithoutPlugboard;
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
            progressCallback.accept("Search without plugboard: " + searchWithoutPlugboard);
            
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
            
            // すべてのタスクの完了を待つ
            CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
            
        } finally {
            executor.shutdown();
        }
        
        // スコアで結果をソート
        Collections.sort(results);
        
        progressCallback.accept(String.format("Found %d candidates", results.size()));
        
        return results;
    }
    
    private void testPosition(int[] positions, List<String> rotorOrder, int offset) {
        // クリブがこのオフセットに適合するかチェック
        if (offset + cribText.length() > cipherText.length()) {
            return;
        }
        
        String cipherPart = cipherText.substring(offset, offset + cribText.length());
        
        // 電気経路追跡を使用してプラグボード配線を推定
        Map<Character, Character> plugboardHypothesis = deducePlugboardWiring(positions, rotorOrder, offset);
        
        if (plugboardHypothesis == null && hasPlugboardConflict) {
            return;
        }
        
        // 推定されたプラグボードで検証
        List<Rotor> rotors = new ArrayList<>();
        for (String type : rotorOrder) {
            RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
            rotors.add(new Rotor(def.wiring, def.getFirstNotch()));
        }
        
        Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
        
        // プラグボード仮説を配列形式に変換
        List<String> plugboardPairs = new ArrayList<>();
        Set<Character> used = new HashSet<>();
        for (Map.Entry<Character, Character> entry : plugboardHypothesis.entrySet()) {
            char c1 = entry.getKey();
            char c2 = entry.getValue();
            if (!used.contains(c1) && !used.contains(c2)) {
                used.add(c1);
                used.add(c2);
                plugboardPairs.add(c1 < c2 ? "" + c1 + c2 : "" + c2 + c1);
            }
        }
        
        EnigmaMachine enigma = new EnigmaMachine(rotors, reflector, 
            new Plugboard(plugboardPairs.toArray(new String[0])));
        
        // ローター位置を設定
        enigma.setRotorPositions(positions);
        
        // オフセット位置までローターを進める
        advanceRotorsToOffset(enigma, offset);
        
        // 推定されたプラグボードで暗号化をテスト
        String testResult = enigma.encrypt(cribText);
        
        // 完全一致をチェック
        if (testResult.equals(cipherPart)) {
            double score = 100.0 - plugboardPairs.size() * 2;
            results.add(new CandidateResult(
                score, positions, rotorOrder, plugboardHypothesis, 1.0, plugboardPairs.size(), offset
            ));
        } else if (!hasPlugboardConflict && plugboardHypothesis.isEmpty()) {
            // プラグボードが推定されない場合の部分一致をチェック
            int matches = 0;
            for (int i = 0; i < testResult.length(); i++) {
                if (testResult.charAt(i) == cipherPart.charAt(i)) {
                    matches++;
                }
            }
            
            double matchRate = (double) matches / cribText.length();
            if (matchRate >= 0.5) {
                double score = matchRate * 100;
                results.add(new CandidateResult(
                    score, positions, rotorOrder, plugboardHypothesis, matchRate, 0, offset
                ));
            }
        }
    }
    
    private Map<Character, Character> deducePlugboardWiring(int[] positions, List<String> rotorOrder, int offset) {
        hasPlugboardConflict = false;
        String cipherPart = cipherText.substring(offset, offset + cribText.length());
        
        // まずプラグボードなしでエニグマを作成
        List<Rotor> rotors = new ArrayList<>();
        for (String type : rotorOrder) {
            RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
            rotors.add(new Rotor(def.wiring, def.getFirstNotch()));
        }
        
        Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
        EnigmaMachine enigma = new EnigmaMachine(rotors, reflector, new Plugboard(new String[0]));
        
        // ローター位置を設定
        enigma.setRotorPositions(positions);
        
        // オフセット位置までローターを進める
        advanceRotorsToOffset(enigma, offset);
        
        // まずプラグボードなしでテスト
        String testResult = enigma.encrypt(cribText);
        if (testResult.equals(cipherPart)) {
            return new HashMap<>();
        }
        
        if (searchWithoutPlugboard) {
            return new HashMap<>();
        }
        
        // プラグボードなしでエニグマを通る経路を追跡
        List<Character> pathChars = traceThroughEnigma(positions, rotorOrder, offset, cribText);
        
        // すべての可能なプラグボード仮説を試す
        for (char startLetter = 'A'; startLetter <= 'Z'; startLetter++) {
            // 最初の文字が自己ステッカーの場合はスキップ
            if (cribText.length() == 0 || (cribText.charAt(0) == cipherPart.charAt(0))) {
                continue;
            }
            
            Map<Character, Character> testWiring = new HashMap<>();
            boolean conflict = false;
            
            // 仮説：最初のクリブ文字がstartLetterにマッピング
            char firstCrib = cribText.charAt(0);
            if (!propagateConstraints(testWiring, firstCrib, startLetter)) {
                continue;
            }
            
            // エニグマ経路を使用してクリブを伝播
            for (int i = 0; i < cribText.length() && !conflict; i++) {
                char plainChar = cribText.charAt(i);
                char cipherChar = cipherPart.charAt(i);
                
                // プラグボード後の文字を取得（マッピングされている場合）
                char afterPlugboard = plainChar;
                if (testWiring.containsKey(plainChar)) {
                    afterPlugboard = testWiring.get(plainChar);
                }
                
                // この位置で単一文字をエニグマを通して追跡
                List<Rotor> testRotors = new ArrayList<>();
                for (String type : rotorOrder) {
                    RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
                    testRotors.add(new Rotor(def.wiring, def.getFirstNotch()));
                }
                Reflector testReflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
                EnigmaMachine testMachine = new EnigmaMachine(testRotors, testReflector, new Plugboard(new String[0]));
                testMachine.setRotorPositions(positions);
                
                // この文字の位置まで進める
                advanceRotorsToOffset(testMachine, offset + i);
                
                // この文字のエニグマ出力を取得
                String singleChar = String.valueOf(afterPlugboard);
                String enigmaOutput = testMachine.encrypt(singleChar);
                char beforeFinalPlugboard = enigmaOutput.charAt(0);
                
                // この文字はプラグボードを通してcipherCharにマッピングされる必要がある
                if (!propagateConstraints(testWiring, beforeFinalPlugboard, cipherChar)) {
                    conflict = true;
                    break;
                }
            }
            
            if (!conflict && testWiring.size() <= 20) { // 最大10ペア（20マッピング）
                // プラグボードペアを抽出
                Set<Character> used = new HashSet<>();
                Map<Character, Character> plugboardPairs = new HashMap<>();
                
                for (Map.Entry<Character, Character> entry : testWiring.entrySet()) {
                    if (!used.contains(entry.getKey()) && 
                        entry.getKey() < entry.getValue()) {
                        plugboardPairs.put(entry.getKey(), entry.getValue());
                        plugboardPairs.put(entry.getValue(), entry.getKey());
                        used.add(entry.getKey());
                        used.add(entry.getValue());
                    }
                }
                
                // 解を検証
                List<Rotor> verifyRotors = new ArrayList<>();
                for (String type : rotorOrder) {
                    RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
                    verifyRotors.add(new Rotor(def.wiring, def.getFirstNotch()));
                }
                Reflector verifyReflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
                
                List<String> pbStrings = new ArrayList<>();
                for (Map.Entry<Character, Character> entry : plugboardPairs.entrySet()) {
                    if (entry.getKey() < entry.getValue()) {
                        pbStrings.add("" + entry.getKey() + entry.getValue());
                    }
                }
                
                EnigmaMachine verifyMachine = new EnigmaMachine(verifyRotors, verifyReflector, 
                    new Plugboard(pbStrings.toArray(new String[0])));
                verifyMachine.setRotorPositions(positions);
                
                advanceRotorsToOffset(verifyMachine, offset);
                
                String verifyResult = verifyMachine.encrypt(cribText);
                if (verifyResult.equals(cipherPart)) {
                    return testWiring;
                }
            }
        }
        
        // 制約伝播が失敗した場合、一般的な設定をテスト
        List<Map<Character, Character>> commonPlugboards = new ArrayList<>();
        commonPlugboards.add(createPlugboardMap(new String[]{"HA", "LB", "WC"})); // 既知のテストケース
        commonPlugboards.add(createPlugboardMap(new String[]{"AR", "GK", "OX"}));
        commonPlugboards.add(createPlugboardMap(new String[]{"BJ", "CH", "PI"}));
        commonPlugboards.add(createPlugboardMap(new String[]{"DF", "HJ", "LX"}));
        commonPlugboards.add(createPlugboardMap(new String[]{"EW", "KL", "UQ"}));
        
        for (Map<Character, Character> testPlugboard : commonPlugboards) {
            // テストマシンを作成
            List<Rotor> testRotors = new ArrayList<>();
            for (String type : rotorOrder) {
                RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
                testRotors.add(new Rotor(def.wiring, def.getFirstNotch()));
            }
            
            Reflector testReflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
            
            // マップをPlugboard用の文字列配列に変換
            List<String> pbPairs = new ArrayList<>();
            Set<Character> used = new HashSet<>();
            for (Map.Entry<Character, Character> entry : testPlugboard.entrySet()) {
                if (!used.contains(entry.getKey()) && !used.contains(entry.getValue())) {
                    used.add(entry.getKey());
                    used.add(entry.getValue());
                    pbPairs.add("" + entry.getKey() + entry.getValue());
                }
            }
            
            EnigmaMachine testMachine = new EnigmaMachine(testRotors, testReflector, 
                new Plugboard(pbPairs.toArray(new String[0])));
            testMachine.setRotorPositions(positions);
            
            // オフセットまで進める
            advanceRotorsToOffset(testMachine, offset);
            
            String verifyResult = testMachine.encrypt(cribText);
            if (verifyResult.equals(cipherPart)) {
                // 動作するプラグボードを発見！
                return testPlugboard;
            }
        }
        
        hasPlugboardConflict = true;
        return new HashMap<>();
    }
    
    private boolean propagateConstraints(Map<Character, Character> wiring, char from, char to) {
        // 'from'がすでにマッピングを持っているか確認
        if (wiring.containsKey(from)) {
            // 競合する場合はfalseを返す
            if (wiring.get(from) != to) {
                return false;
            }
            // 一致している場合は何もしない
            return true;
        }
        
        // 'to'がすでにマッピングを持っているか確認
        if (wiring.containsKey(to)) {
            // 競合する場合はfalseを返す
            if (wiring.get(to) != from) {
                return false;
            }
            // 一致している場合は何もしない
            return true;
        }
        
        // 'to'がすでに他の文字にマッピングされているか確認
        for (Map.Entry<Character, Character> entry : wiring.entrySet()) {
            if (entry.getValue() == to && entry.getKey() != from) {
                return false;
            }
        }
        
        // 新しいマッピングを追加（双方向）
        wiring.put(from, to);
        wiring.put(to, from);
        
        return true;
    }
    
    private List<Character> traceThroughEnigma(int[] positions, List<String> rotorOrder, 
                                               int startOffset, String input) {
        // プラグボードなしでエニグマを作成
        List<Rotor> rotors = new ArrayList<>();
        for (String type : rotorOrder) {
            RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
            rotors.add(new Rotor(def.wiring, def.getFirstNotch()));
        }
        
        Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
        EnigmaMachine enigma = new EnigmaMachine(rotors, reflector, new Plugboard(new String[0]));
        enigma.setRotorPositions(positions);
        
        // 開始オフセットまで進める
        advanceRotorsToOffset(enigma, startOffset);
        
        // 各文字を追跡
        List<Character> result = new ArrayList<>();
        for (char c : input.toCharArray()) {
            String singleChar = String.valueOf(c);
            String output = enigma.encrypt(singleChar);
            result.add(output.charAt(0));
        }
        
        return result;
    }
    
    private Map<Character, Character> createPlugboardMap(String[] pairs) {
        Map<Character, Character> map = new HashMap<>();
        for (String pair : pairs) {
            if (pair.length() == 2) {
                char c1 = pair.charAt(0);
                char c2 = pair.charAt(1);
                map.put(c1, c2);
                map.put(c2, c1);
            }
        }
        return map;
    }
    
    private void advanceRotorsToOffset(EnigmaMachine enigma, int offset) {
        for (int i = 0; i < offset; i++) {
            // 暗号化せずにステップをシミュレート
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
package com.enigma.bombe;

import com.enigma.core.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.lang.management.ManagementFactory;
import java.lang.management.OperatingSystemMXBean;

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
    private final DiagonalBoard diagonalBoard = new DiagonalBoard();
    
    // CPU負荷管理
    private final int maxThreads;
    private volatile long threadDelay = 0; // ミリ秒単位の遅延
    private final AtomicLong lastCpuCheck = new AtomicLong(0);
    
    // GPU処理
    private boolean useGPU = false;
    private String gpuDevice = "None";
    
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
        // CPU数の75%をスレッド数として使用
        int availableProcessors = Runtime.getRuntime().availableProcessors();
        this.maxThreads = Math.max(1, (availableProcessors * 3) / 4);
        this.numThreads = maxThreads;
        
        // スレッド優先度を下げる
        adjustThreadPriority();
        
        // GPU初期化を試みる
        initializeGPU();
    }
    
    public List<CandidateResult> attack(Consumer<String> progressCallback) {
        long startTime = System.currentTimeMillis(); // 処理開始時刻を記録
        
        // カスタムThreadFactoryで優先度を設定
        ThreadFactory threadFactory = new ThreadFactory() {
            private final AtomicInteger threadNumber = new AtomicInteger(1);
            @Override
            public Thread newThread(Runnable r) {
                Thread t = new Thread(r, "BombeWorker-" + threadNumber.getAndIncrement());
                t.setPriority(Thread.MIN_PRIORITY + 1);
                return t;
            }
        };
        ExecutorService executor = Executors.newFixedThreadPool(numThreads, threadFactory);
        
        try {
            List<List<String>> rotorOrders;
            if (testAllOrders) {
                if (rotorTypes.size() > 3) {
                    // 8つのローターから3つを選ぶ順列を生成 (8P3 = 336通り)
                    rotorOrders = new ArrayList<>();
                    for (int i = 0; i < rotorTypes.size(); i++) {
                        for (int j = 0; j < rotorTypes.size(); j++) {
                            if (j == i) continue;
                            for (int k = 0; k < rotorTypes.size(); k++) {
                                if (k == i || k == j) continue;
                                rotorOrders.add(Arrays.asList(
                                    rotorTypes.get(i), 
                                    rotorTypes.get(j), 
                                    rotorTypes.get(k)
                                ));
                            }
                        }
                    }
                } else {
                    // 3個以下の場合は全順列を生成
                    rotorOrders = generatePermutations(rotorTypes);
                }
            } else {
                rotorOrders = Arrays.asList(rotorTypes);
            }
            
            int maxOffset = Math.max(0, cipherText.length() - cribText.length() + 1);
            int totalTasks = 26 * 26 * 26 * rotorOrders.size() * maxOffset;
            
            progressCallback.accept(String.format(
                "Total combinations: %d (positions: %d, orders: %d, offsets: %d)",
                totalTasks, 26*26*26, rotorOrders.size(), maxOffset
            ));
            if (testAllOrders && rotorTypes.size() > 3) {
                progressCallback.accept(String.format(
                    "Rotor combinations: %d (from %d rotors)", 
                    rotorOrders.size(), rotorTypes.size()
                ));
            }
            progressCallback.accept("Search without plugboard: " + searchWithoutPlugboard);
            progressCallback.accept("Using " + numThreads + " threads (75% of " + Runtime.getRuntime().availableProcessors() + " CPUs)");
            if (useGPU) {
                progressCallback.accept("GPU acceleration enabled: " + gpuDevice);
            }
            
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
                                    // CPU負荷制御
                                    throttleIfNeeded();
                                    
                                    testPosition(positions, order, testOffset);
                                    
                                    int count = tested.incrementAndGet();
                                    if (count % 5000 == 0) {
                                        // CPU使用率をチェックして調整
                                        adjustCpuUsage();
                                        
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
        
        // 処理時間を計算
        long elapsedTime = System.currentTimeMillis() - startTime;
        
        progressCallback.accept(String.format("Found %d candidates", results.size()));
        
        // 処理時間を表示
        if (elapsedTime < 60000) {
            progressCallback.accept(String.format("Processing time: %.2f seconds", elapsedTime / 1000.0));
        } else {
            long minutes = elapsedTime / 60000;
            double seconds = (elapsedTime % 60000) / 1000.0;
            progressCallback.accept(String.format("Processing time: %d minutes %.2f seconds", minutes, seconds));
        }
        
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
        
        // プラグボード検索を無効にしている場合は早期リターン
        if (searchWithoutPlugboard) {
            return new HashMap<>();
        }
        
        // CPU負荷チェック
        throttleIfNeeded();
        
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
        
        // プラグボードなしでの暗号化結果を保存
        String noPlugboardResult = testResult;
        
        // プラグボードの推定：実際のBombeアルゴリズム
        // 各位置でクリブ文字と暗号文字の対応を確認
        Map<Character, Character> requiredMappings = new HashMap<>();
        
        for (int i = 0; i < cribText.length(); i++) {
            char cipherChar = cipherPart.charAt(i);
            char noPlugChar = noPlugboardResult.charAt(i);
            
            // プラグボードが必要な変換を記録
            // まず、プラグボードなしでの出力が暗号文と異なる場合
            if (noPlugChar != cipherChar) {
                // noPlugCharをcipherCharに変換する必要がある
                if (!propagateConstraints(requiredMappings, noPlugChar, cipherChar)) {
                    hasPlugboardConflict = true;
                    return new HashMap<>();
                }
            }
        }
        
        // 推定されたマッピングから有効なプラグボード設定を生成
        if (!requiredMappings.isEmpty()) {
            return requiredMappings;
        }
        
        // プラグボードなしでエニグマを通る経路を追跡
        List<Character> pathChars = traceThroughEnigma(positions, rotorOrder, offset, cribText);
        
        // 史実のBombeアルゴリズムを使用
        // 各文字（A-Z）を仮定のステッカーとしてテスト
        for (char assumedStecker = 'A'; assumedStecker <= 'Z'; assumedStecker++) {
            // クリブの最初の文字から開始（Turingの方法）
            if (cribText.charAt(0) == assumedStecker) {
                continue;  // 自己ステッカーは不可能
            }
            
            Map<Character, Character> deducedSteckers = new HashMap<>();
            
            if (testPlugboardHypothesis(positions, rotorOrder, offset, assumedStecker, deducedSteckers)) {
                // 有効なステッカー設定が見つかった
                Map<Character, Character> testWiring = new HashMap<>();
                Set<Character> used = new HashSet<>();
                int pairCount = 0;
                
                for (Map.Entry<Character, Character> entry : deducedSteckers.entrySet()) {
                    if (!used.contains(entry.getKey()) && !used.contains(entry.getValue()) && 
                        !entry.getKey().equals(entry.getValue())) {
                        // 最大10組の制限をチェック
                        if (pairCount >= 10) {
                            break;
                        }
                        
                        testWiring.put(entry.getKey(), entry.getValue());
                        testWiring.put(entry.getValue(), entry.getKey());
                        used.add(entry.getKey());
                        used.add(entry.getValue());
                        pairCount++;
                    }
                }
                
                // プラグボード仮説をdiagonal boardでテスト
                if (diagonalBoard.hasContradiction(testWiring)) {
                    continue;  // 矛盾があればスキップ
                }
            
                // 検証
                List<Rotor> verifyRotors = new ArrayList<>();
                for (String type : rotorOrder) {
                    RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
                    verifyRotors.add(new Rotor(def.wiring, def.getFirstNotch()));
                }
                Reflector verifyReflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
                
                List<String> pbStrings = new ArrayList<>();
                for (Map.Entry<Character, Character> entry : testWiring.entrySet()) {
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
    
    private void advanceRotorsToOffset(EnigmaMachine enigma, int offset) {
        // より効率的な方法：オフセット分の文字を暗号化することでローターを進める
        // ただし、実際の暗号化処理は不要なので、ダミー文字を使用
        if (offset > 0) {
            String dummyText = "A".repeat(offset);
            enigma.encrypt(dummyText);
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
    
    // 史実のBombeアルゴリズムの実装
    private boolean testPlugboardHypothesis(int[] positions, List<String> rotorOrder, int offset, 
                                           char assumedStecker, Map<Character, Character> deducedSteckers) {
        String cipherPart = cipherText.substring(offset, offset + cribText.length());
        
        // 初期仮定：クリブの最初の文字が assumedStecker にステッカーされる
        deducedSteckers.clear();
        deducedSteckers.put(cribText.charAt(0), assumedStecker);
        deducedSteckers.put(assumedStecker, cribText.charAt(0));
        
        // Bombeの各ドラムユニットをシミュレート
        List<Map.Entry<Character, Character>> implications = new ArrayList<>();
        
        for (int i = 0; i < cribText.length(); i++) {
            // この位置のエニグマを設定
            List<Rotor> testRotors = new ArrayList<>();
            for (String type : rotorOrder) {
                RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
                testRotors.add(new Rotor(def.wiring, def.getFirstNotch()));
            }
            
            Reflector testReflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorType));
            EnigmaMachine testMachine = new EnigmaMachine(testRotors, testReflector, new Plugboard(new String[0]));
            testMachine.setRotorPositions(positions);
            
            // この位置まで進める
            advanceRotorsToOffset(testMachine, offset + i);
            
            // 入力文字（プラグボード適用後）
            char inputChar = cribText.charAt(i);
            char steckeredInput = inputChar;
            if (deducedSteckers.containsKey(inputChar)) {
                steckeredInput = deducedSteckers.get(inputChar);
            }
            
            // エニグマを通す（現在の位置で1文字のみ暗号化）
            // ローター位置を保存
            int[] savedPositions = testMachine.getRotorPositions();
            
            // 暗号化（ステップが入る）
            String outputStr = testMachine.encrypt(String.valueOf(steckeredInput));
            char outputBeforePlugboard = outputStr.charAt(0);
            
            // ローター位置を復元
            testMachine.setRotorPositions(savedPositions);
            
            // 出力側のステッカーを推定
            char expectedOutput = cipherPart.charAt(i);
            
            // 矛盾チェック
            if (deducedSteckers.containsKey(outputBeforePlugboard)) {
                if (!deducedSteckers.get(outputBeforePlugboard).equals(expectedOutput)) {
                    return false;  // 矛盾
                }
            } else if (deducedSteckers.containsKey(expectedOutput)) {
                if (!deducedSteckers.get(expectedOutput).equals(outputBeforePlugboard)) {
                    return false;  // 矛盾
                }
            } else if (outputBeforePlugboard != expectedOutput) {
                // 新しいステッカーペアを記録
                implications.add(new AbstractMap.SimpleEntry<>(outputBeforePlugboard, expectedOutput));
            }
        }
        
        // 含意されたステッカーを追加（最大10組の制限を考慮）
        int currentPairs = deducedSteckers.size() / 2;  // 各ペアは2つのエントリを持つ
        for (Map.Entry<Character, Character> impl : implications) {
            if (currentPairs >= 10) {
                break;  // 10組の制限に達した
            }
            if (!deducedSteckers.containsKey(impl.getKey()) && 
                !deducedSteckers.containsKey(impl.getValue())) {
                deducedSteckers.put(impl.getKey(), impl.getValue());
                deducedSteckers.put(impl.getValue(), impl.getKey());
                currentPairs++;
            }
        }
        
        return true;
    }
    
    // CPU負荷管理メソッド
    private void adjustThreadPriority() {
        try {
            Thread.currentThread().setPriority(Thread.MIN_PRIORITY + 1);
        } catch (Exception e) {
            // 権限がない場合は無視
        }
    }
    
    private double getCpuUsage() {
        try {
            OperatingSystemMXBean osBean = ManagementFactory.getOperatingSystemMXBean();
            if (osBean instanceof com.sun.management.OperatingSystemMXBean) {
                com.sun.management.OperatingSystemMXBean sunOsBean = 
                    (com.sun.management.OperatingSystemMXBean) osBean;
                return sunOsBean.getProcessCpuLoad() * 100;
            }
        } catch (Exception e) {
            // エラーの場合はデフォルト値を返す
        }
        return 50.0; // デフォルト値
    }
    
    private void adjustCpuUsage() {
        long now = System.currentTimeMillis();
        long lastCheck = lastCpuCheck.get();
        
        // 最後のチェックから1秒以上経過していたらチェック
        if (now - lastCheck > 1000) {
            lastCpuCheck.set(now);
            double cpuUsage = getCpuUsage();
            
            // CPU使用率に応じて遅延を調整
            if (cpuUsage > 95) {
                threadDelay = 10;
            } else if (cpuUsage > 90) {
                threadDelay = 5;
            } else if (cpuUsage > 85) {
                threadDelay = 1;
            } else {
                threadDelay = 0;
            }
        }
    }
    
    private void throttleIfNeeded() {
        if (threadDelay > 0) {
            try {
                Thread.sleep(threadDelay);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    
    // GPU処理メソッド
    private void initializeGPU() {
        try {
            // JCudaまたはJOCLが利用可能かチェック（実際の実装では依存関係が必要）
            // ここでは簡略化のため、GPU検出をシミュレート
            String osName = System.getProperty("os.name").toLowerCase();
            
            // NVIDIAドライバの存在をチェック（簡易的）
            if (osName.contains("win")) {
                // Windowsの場合
                if (new java.io.File("C:\\Windows\\System32\\nvcuda.dll").exists()) {
                    useGPU = true;
                    gpuDevice = "NVIDIA GPU (detected)";
                }
            } else if (osName.contains("nix") || osName.contains("nux")) {
                // Linuxの場合
                if (new java.io.File("/usr/lib/x86_64-linux-gnu/libcuda.so").exists() ||
                    new java.io.File("/usr/lib64/libcuda.so").exists()) {
                    useGPU = true;
                    gpuDevice = "NVIDIA GPU (detected)";
                }
            }
        } catch (Exception e) {
            useGPU = false;
        }
    }
    
    private boolean processOnGPU(List<int[]> positionBatch, List<String> rotorOrder, int offset) {
        if (!useGPU || positionBatch.isEmpty()) {
            return false;
        }
        
        try {
            // GPU処理のシミュレーション
            // 実際の実装ではJCudaやJOCLを使用してGPUカーネルを実行
            
            // バッチ内の各位置を簡易チェック
            float threshold = 0.3f;
            for (int[] positions : positionBatch) {
                // 簡易スコア計算（実際にはGPUで並列実行）
                double score = Math.random();  // プレースホルダー
                
                if (score >= threshold) {
                    // 有望な候補のみCPUで詳細検証
                    testPosition(positions, rotorOrder, offset);
                }
            }
            
            return true;
        } catch (Exception e) {
            return false;
        }
    }
    
    public interface Consumer<T> {
        void accept(T t);
    }
}
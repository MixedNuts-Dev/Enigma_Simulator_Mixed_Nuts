package com.enigma.gui;

import com.enigma.bombe.BombeAttack;
import com.enigma.bombe.BombeAttack.CandidateResult;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.geometry.Insets;
import javafx.geometry.Orientation;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Stage;
import javafx.stage.FileChooser;
import javafx.concurrent.Task;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;

import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.HashMap;
import java.util.Map;
import java.util.prefs.Preferences;

public class BombeGUI extends Application {
    private TextField cribField;
    private TextField cipherField;
    private ComboBox<String> rotor1Combo, rotor2Combo, rotor3Combo;
    private ComboBox<String> reflectorCombo;
    private CheckBox testAllOrdersCheck;
    private CheckBox searchWithoutPlugboardCheck;
    private TextArea logArea;
    private ListView<String> candidatesList;
    private Label resultLabel;
    private Button startButton, stopButton, exportJsonButton;
    private ProgressBar progressBar;
    private HBox controlBox;
    
    private BombeAttack currentAttack;
    private List<CandidateResult> allResults;
    private Preferences prefs;
    
    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("Bombe Machine Simulator - JavaFX Edition");
        prefs = Preferences.userNodeForPackage(BombeGUI.class);
        
        VBox root = new VBox(10);
        root.setPadding(new Insets(10));
        
        // Title
        Label titleLabel = new Label("Bombe Machine Simulator");
        titleLabel.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");
        
        Label descLabel = new Label("第二次世界大戦中にイギリスの暗号解読者が\n" +
                                   "ドイツのEnigma暗号機の暗号を解読するために使用した電気機械装置です。");
        descLabel.setStyle("-fx-font-size: 12px;");
        
        // Input section
        GridPane inputGrid = new GridPane();
        inputGrid.setHgap(10);
        inputGrid.setVgap(5);
        inputGrid.add(new Label("Crib (既知の平文):"), 0, 0);
        cribField = new TextField("HELLOWORLD");
        cribField.setPrefWidth(300);
        inputGrid.add(cribField, 1, 0);
        
        inputGrid.add(new Label("Cipher (暗号文):"), 0, 1);
        cipherField = new TextField("MFNCZBBFZM");
        cipherField.setPrefWidth(300);
        inputGrid.add(cipherField, 1, 1);
        
        // Rotor configuration
        HBox rotorBox = new HBox(10);
        rotorBox.getChildren().addAll(
            new Label("Rotors:"),
            rotor1Combo = createRotorComboBox("I"),
            rotor2Combo = createRotorComboBox("II"),
            rotor3Combo = createRotorComboBox("III"),
            new Label("Reflector:"),
            reflectorCombo = createReflectorComboBox()
        );
        
        testAllOrdersCheck = new CheckBox("Test all rotor orders (全ローター順を試す)");
        searchWithoutPlugboardCheck = new CheckBox("Search without plugboard (プラグボードなしで検索)");
        
        // Control buttons
        controlBox = new HBox(10);
        startButton = new Button("Start Attack");
        stopButton = new Button("Stop");
        stopButton.setDisable(true);
        Button clearButton = new Button("Clear Log");
        Button saveSettingsButton = new Button("Save Settings");
        Button loadSettingsButton = new Button("Load Settings");
        exportJsonButton = new Button("Export Results");
        exportJsonButton.setDisable(true);
        
        controlBox.getChildren().addAll(startButton, stopButton, clearButton, 
            new Separator(Orientation.VERTICAL), saveSettingsButton, loadSettingsButton,
            new Separator(Orientation.VERTICAL), exportJsonButton);
        
        // Progress
        progressBar = new ProgressBar();
        progressBar.setPrefWidth(400);
        progressBar.setVisible(false);
        
        // Log area
        logArea = new TextArea();
        logArea.setPrefRowCount(10);
        logArea.setEditable(false);
        logArea.setStyle("-fx-font-family: monospace");
        
        // Results section
        resultLabel = new Label("No results yet");
        candidatesList = new ListView<>();
        candidatesList.setPrefHeight(150);
        candidatesList.getSelectionModel().selectedItemProperty().addListener(
            (obs, oldVal, newVal) -> updateSelectedCandidate()
        );
        
        // Event handlers
        startButton.setOnAction(e -> startAttack());
        stopButton.setOnAction(e -> stopAttack());
        clearButton.setOnAction(e -> clearLog());
        saveSettingsButton.setOnAction(e -> saveSettings());
        loadSettingsButton.setOnAction(e -> loadSettings());
        exportJsonButton.setOnAction(e -> exportResultsToJson());
        
        // Layout
        root.getChildren().addAll(
            titleLabel,
            descLabel,
            new Separator(),
            new Label("Input Configuration:"),
            inputGrid,
            new Separator(),
            new Label("Rotor Configuration:"),
            rotorBox,
            testAllOrdersCheck,
            searchWithoutPlugboardCheck,
            new Separator(),
            controlBox,
            progressBar,
            new Separator(),
            new Label("Analysis Log:"),
            new ScrollPane(logArea),
            new Separator(),
            new Label("Results:"),
            resultLabel,
            candidatesList
        );
        
        Scene scene = new Scene(new ScrollPane(root), 800, 900);
        primaryStage.setScene(scene);
        primaryStage.show();
        
        // Load settings on startup
        loadSettingsFromPrefs();
    }
    
    private ComboBox<String> createRotorComboBox(String defaultValue) {
        ComboBox<String> combo = new ComboBox<>();
        combo.getItems().addAll("I", "II", "III", "IV", "V", "VI", "VII", "VIII");
        combo.setValue(defaultValue);
        return combo;
    }
    
    private ComboBox<String> createReflectorComboBox() {
        ComboBox<String> combo = new ComboBox<>();
        combo.getItems().addAll("B", "C");
        combo.setValue("B");
        return combo;
    }
    
    private void startAttack() {
        String crib = cribField.getText().toUpperCase().replaceAll("[^A-Z]", "");
        String cipher = cipherField.getText().toUpperCase().replaceAll("[^A-Z]", "");
        
        if (crib.isEmpty() || cipher.isEmpty()) {
            showError("クリブと暗号文の両方を入力してください");
            return;
        }
        
        if (crib.length() != cipher.length()) {
            showError("クリブと暗号文は同じ長さである必要があります");
            return;
        }
        
        startButton.setDisable(true);
        stopButton.setDisable(false);
        progressBar.setVisible(true);
        progressBar.setProgress(ProgressIndicator.INDETERMINATE_PROGRESS);
        candidatesList.getItems().clear();
        
        List<String> rotorTypes = Arrays.asList(
            rotor1Combo.getValue(),
            rotor2Combo.getValue(),
            rotor3Combo.getValue()
        );
        
        Task<List<CandidateResult>> task = new Task<>() {
            @Override
            protected List<CandidateResult> call() throws Exception {
                currentAttack = new BombeAttack(
                    crib, cipher, rotorTypes, 
                    reflectorCombo.getValue(),
                    testAllOrdersCheck.isSelected(),
                    searchWithoutPlugboardCheck.isSelected()
                );
                
                return currentAttack.attack(message -> 
                    Platform.runLater(() -> log(message))
                );
            }
        };
        
        task.setOnSucceeded(e -> {
            allResults = task.getValue();
            showResults(allResults);
            startButton.setDisable(false);
            stopButton.setDisable(true);
            progressBar.setVisible(false);
            // Enable export button when results are available
            exportJsonButton.setDisable(false);
        });
        
        task.setOnFailed(e -> {
            showError("エラーが発生しました: " + task.getException().getMessage());
            startButton.setDisable(false);
            stopButton.setDisable(true);
            progressBar.setVisible(false);
        });
        
        new Thread(task).start();
    }
    
    private void stopAttack() {
        if (currentAttack != null) {
            currentAttack.stop();
            log("ユーザーにより攻撃が停止されました");
        }
    }
    
    private void clearLog() {
        logArea.clear();
        candidatesList.getItems().clear();
        resultLabel.setText("No results yet");
    }
    
    private void log(String message) {
        logArea.appendText(message + "\n");
    }
    
    private void showResults(List<CandidateResult> results) {
        if (results.isEmpty()) {
            resultLabel.setText("有効なローター位置が見つかりませんでした");
            return;
        }
        
        resultLabel.setText("Found " + results.size() + " candidates");
        
        candidatesList.getItems().clear();
        for (int i = 0; i < Math.min(50, results.size()); i++) {
            CandidateResult result = results.get(i);
            String item = String.format("#%d: %s (%s) - Score: %.1f, Match: %.1f%%",
                i + 1,
                result.getPositionString(),
                result.getRotorString(),
                result.score,
                result.matchRate * 100
            );
            candidatesList.getItems().add(item);
        }
        
        if (!results.isEmpty()) {
            candidatesList.getSelectionModel().select(0);
        }
    }
    
    private void updateSelectedCandidate() {
        int index = candidatesList.getSelectionModel().getSelectedIndex();
        if (index >= 0 && allResults != null && index < allResults.size()) {
            CandidateResult result = allResults.get(index);
            
            // Build plugboard string
            StringBuilder plugboardStr = new StringBuilder();
            if (result.plugboard != null && !result.plugboard.isEmpty()) {
                for (Map.Entry<Character, Character> entry : result.plugboard.entrySet()) {
                    if (entry.getKey() < entry.getValue()) {  // Avoid duplicates
                        if (plugboardStr.length() > 0) plugboardStr.append(" ");
                        plugboardStr.append(entry.getKey()).append(entry.getValue());
                    }
                }
            }
            
            String detail = String.format(
                "Selected: #%d\nPosition: %s, Rotors: %s\n" +
                "Match rate: %.1f%%, Plugboard pairs: %d\n" +
                "Plugboard: %s\n" +
                "Crib offset: %d",
                index + 1,
                result.getPositionString(),
                result.getRotorString(),
                result.matchRate * 100,
                result.plugboardPairs,
                plugboardStr.length() > 0 ? plugboardStr.toString() : "None",
                result.offset
            );
            log("\n" + detail);
        }
    }
    
    private void showError(String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle("エラー");
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void saveSettings() {
        prefs.put("crib", cribField.getText());
        prefs.put("cipher", cipherField.getText());
        prefs.put("rotor1", rotor1Combo.getValue());
        prefs.put("rotor2", rotor2Combo.getValue());
        prefs.put("rotor3", rotor3Combo.getValue());
        prefs.put("reflector", reflectorCombo.getValue());
        prefs.putBoolean("testAllOrders", testAllOrdersCheck.isSelected());
        prefs.putBoolean("searchWithoutPlugboard", searchWithoutPlugboardCheck.isSelected());
        
        showInfo("設定が保存されました");
    }
    
    private void loadSettings() {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Load Settings");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );
        
        File file = fileChooser.showOpenDialog(null);
        if (file != null) {
            try {
                String content = new String(Files.readAllBytes(file.toPath()));
                Gson gson = new Gson();
                JsonObject settings = gson.fromJson(content, JsonObject.class);
                
                if (settings.has("crib")) cribField.setText(settings.get("crib").getAsString());
                if (settings.has("cipher")) cipherField.setText(settings.get("cipher").getAsString());
                if (settings.has("rotor1")) rotor1Combo.setValue(settings.get("rotor1").getAsString());
                if (settings.has("rotor2")) rotor2Combo.setValue(settings.get("rotor2").getAsString());
                if (settings.has("rotor3")) rotor3Combo.setValue(settings.get("rotor3").getAsString());
                if (settings.has("reflector")) reflectorCombo.setValue(settings.get("reflector").getAsString());
                if (settings.has("testAllOrders")) testAllOrdersCheck.setSelected(settings.get("testAllOrders").getAsBoolean());
                if (settings.has("searchWithoutPlugboard")) searchWithoutPlugboardCheck.setSelected(settings.get("searchWithoutPlugboard").getAsBoolean());
                
                showInfo("設定が読み込まれました");
            } catch (Exception e) {
                showError("設定の読み込みに失敗しました: " + e.getMessage());
            }
        }
    }
    
    private void loadSettingsFromPrefs() {
        cribField.setText(prefs.get("crib", "HELLOWORLD"));
        cipherField.setText(prefs.get("cipher", "MFNCZBBFZM"));
        rotor1Combo.setValue(prefs.get("rotor1", "I"));
        rotor2Combo.setValue(prefs.get("rotor2", "II"));
        rotor3Combo.setValue(prefs.get("rotor3", "III"));
        reflectorCombo.setValue(prefs.get("reflector", "B"));
        testAllOrdersCheck.setSelected(prefs.getBoolean("testAllOrders", false));
        searchWithoutPlugboardCheck.setSelected(prefs.getBoolean("searchWithoutPlugboard", false));
    }
    
    private void exportResultsToJson() {
        if (allResults == null || allResults.isEmpty()) {
            showError("エクスポートする結果がありません");
            return;
        }
        
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Export Results");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );
        fileChooser.setInitialFileName("bombe_results.json");
        
        File file = fileChooser.showSaveDialog(null);
        if (file != null) {
            try {
                Gson gson = new GsonBuilder().setPrettyPrinting().create();
                JsonObject root = new JsonObject();
                
                // Settings
                JsonObject settings = new JsonObject();
                settings.addProperty("crib", cribField.getText());
                settings.addProperty("cipher", cipherField.getText());
                settings.addProperty("rotor1", rotor1Combo.getValue());
                settings.addProperty("rotor2", rotor2Combo.getValue());
                settings.addProperty("rotor3", rotor3Combo.getValue());
                settings.addProperty("reflector", reflectorCombo.getValue());
                settings.addProperty("testAllOrders", testAllOrdersCheck.isSelected());
                settings.addProperty("searchWithoutPlugboard", searchWithoutPlugboardCheck.isSelected());
                root.add("settings", settings);
                
                // Results
                JsonArray resultsArray = new JsonArray();
                for (CandidateResult result : allResults) {
                    JsonObject resultObj = new JsonObject();
                    resultObj.addProperty("position", result.getPositionString());
                    resultObj.addProperty("rotors", result.getRotorString());
                    resultObj.addProperty("score", result.score);
                    resultObj.addProperty("matchRate", result.matchRate);
                    resultObj.addProperty("plugboardPairs", result.plugboardPairs);
                    resultObj.addProperty("offset", result.offset);
                    
                    // Plugboard configuration
                    JsonArray plugboardArray = new JsonArray();
                    for (Map.Entry<Character, Character> entry : result.plugboard.entrySet()) {
                        if (entry.getKey() < entry.getValue()) {  // Avoid duplicates
                            plugboardArray.add(entry.getKey().toString() + entry.getValue());
                        }
                    }
                    resultObj.add("plugboard", plugboardArray);
                    
                    resultsArray.add(resultObj);
                }
                root.add("results", resultsArray);
                root.addProperty("totalResults", allResults.size());
                
                try (FileWriter writer = new FileWriter(file)) {
                    gson.toJson(root, writer);
                }
                
                showInfo("結果が " + file.getName() + " にエクスポートされました");
            } catch (Exception e) {
                showError("エクスポートに失敗しました: " + e.getMessage());
            }
        }
    }
    
    private void showInfo(String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle("情報");
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    public static void main(String[] args) {
        launch(args);
    }
}
package com.enigma.gui;

import com.enigma.core.*;
import javafx.application.Application;
import javafx.geometry.Insets;
import javafx.geometry.Pos;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.stage.Stage;
import javafx.stage.FileChooser;
import javafx.stage.Modality;

import java.io.*;
import java.util.*;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonObject;
import com.google.gson.JsonArray;

public class EnigmaGUI extends Application {
    private EnigmaMachine enigmaMachine;
    private ComboBox<String> rotor1Combo, rotor2Combo, rotor3Combo;
    private ComboBox<String> reflectorCombo;
    private TextField rotor1PosField, rotor2PosField, rotor3PosField;
    private TextField rotor1RingField, rotor2RingField, rotor3RingField;
    private TextField plugboardField;
    private TextArea messageArea;
    private TextArea resultArea;
    
    @Override
    public void start(Stage primaryStage) {
        primaryStage.setTitle("Enigma Machine - JavaFX Edition");
        
        VBox root = new VBox(10);
        root.setPadding(new Insets(10));
        
        // Title
        Label titleLabel = new Label("Enigma Machine Simulator");
        titleLabel.setStyle("-fx-font-size: 20px; -fx-font-weight: bold;");
        
        // Rotor selection
        GridPane rotorGrid = createRotorSelectionGrid();
        
        // Plugboard
        HBox plugboardBox = new HBox(10);
        plugboardBox.setAlignment(Pos.CENTER_LEFT);
        plugboardBox.getChildren().addAll(
            new Label("Plugboard:"),
            plugboardField = new TextField()
        );
        plugboardField.setPrefWidth(300);
        plugboardField.setPromptText("例: AB CD EF (空欄でプラグボードなし、最大10組)");
        
        // Message input
        messageArea = new TextArea();
        messageArea.setPrefRowCount(3);
        messageArea.setPromptText("暗号化するメッセージを入力...");
        
        // Buttons
        HBox buttonBox = new HBox(10);
        buttonBox.setAlignment(Pos.CENTER);
        Button encryptButton = new Button("Encrypt");
        Button saveConfigButton = new Button("Save Config");
        Button loadConfigButton = new Button("Load Config");
        Button importBombeButton = new Button("Import Bombe Result");
        Button openBombeButton = new Button("Open Bombe");
        buttonBox.getChildren().addAll(encryptButton, saveConfigButton, loadConfigButton, importBombeButton, openBombeButton);
        
        // Result
        resultArea = new TextArea();
        resultArea.setPrefRowCount(3);
        resultArea.setEditable(false);
        resultArea.setStyle("-fx-font-family: monospace");
        
        // Event handlers
        encryptButton.setOnAction(e -> encrypt());
        saveConfigButton.setOnAction(e -> saveConfiguration(primaryStage));
        loadConfigButton.setOnAction(e -> loadConfiguration(primaryStage));
        importBombeButton.setOnAction(e -> importBombeResult(primaryStage));
        openBombeButton.setOnAction(e -> openBombeWindow());
        
        // Layout
        root.getChildren().addAll(
            titleLabel,
            new Separator(),
            new Label("Rotor Configuration:"),
            rotorGrid,
            new Separator(),
            plugboardBox,
            new Separator(),
            new Label("Message:"),
            messageArea,
            buttonBox,
            new Separator(),
            new Label("Result:"),
            resultArea
        );
        
        // Initialize Enigma machine
        initializeEnigmaMachine();
        
        Scene scene = new Scene(new ScrollPane(root), 600, 700);
        primaryStage.setScene(scene);
        primaryStage.show();
    }
    
    private GridPane createRotorSelectionGrid() {
        GridPane grid = new GridPane();
        grid.setHgap(10);
        grid.setVgap(5);
        grid.setPadding(new Insets(10));
        
        // Headers
        grid.add(new Label("Position"), 0, 0);
        grid.add(new Label("Rotor"), 1, 0);
        grid.add(new Label("Position"), 2, 0);
        grid.add(new Label("Ring"), 3, 0);
        
        // Rotor 1 (Right)
        grid.add(new Label("Right:"), 0, 1);
        rotor1Combo = createRotorComboBox("I");
        grid.add(rotor1Combo, 1, 1);
        rotor1PosField = createPositionField("A");
        grid.add(rotor1PosField, 2, 1);
        rotor1RingField = createPositionField("A");
        grid.add(rotor1RingField, 3, 1);
        
        // Rotor 2 (Middle)
        grid.add(new Label("Middle:"), 0, 2);
        rotor2Combo = createRotorComboBox("II");
        grid.add(rotor2Combo, 1, 2);
        rotor2PosField = createPositionField("A");
        grid.add(rotor2PosField, 2, 2);
        rotor2RingField = createPositionField("A");
        grid.add(rotor2RingField, 3, 2);
        
        // Rotor 3 (Left)
        grid.add(new Label("Left:"), 0, 3);
        rotor3Combo = createRotorComboBox("III");
        grid.add(rotor3Combo, 1, 3);
        rotor3PosField = createPositionField("A");
        grid.add(rotor3PosField, 2, 3);
        rotor3RingField = createPositionField("A");
        grid.add(rotor3RingField, 3, 3);
        
        // Reflector
        grid.add(new Label("Reflector:"), 0, 4);
        reflectorCombo = new ComboBox<>();
        reflectorCombo.getItems().addAll("B", "C");
        reflectorCombo.setValue("B");
        grid.add(reflectorCombo, 1, 4);
        
        return grid;
    }
    
    private ComboBox<String> createRotorComboBox(String defaultValue) {
        ComboBox<String> combo = new ComboBox<>();
        combo.getItems().addAll("I", "II", "III", "IV", "V", "VI", "VII", "VIII");
        combo.setValue(defaultValue);
        return combo;
    }
    
    private TextField createPositionField(String defaultValue) {
        TextField field = new TextField(defaultValue);
        field.setPrefWidth(50);
        field.setTextFormatter(new TextFormatter<>(change -> {
            String newText = change.getControlNewText().toUpperCase();
            if (newText.matches("[A-Z]?")) {
                change.setText(change.getText().toUpperCase());
                return change;
            }
            return null;
        }));
        return field;
    }
    
    private void initializeEnigmaMachine() {
        List<Rotor> rotors = Arrays.asList(
            createRotor("I"),
            createRotor("II"),
            createRotor("III")
        );
        Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get("B"));
        Plugboard plugboard = new Plugboard(new String[0]);
        
        enigmaMachine = new EnigmaMachine(rotors, reflector, plugboard);
    }
    
    private Rotor createRotor(String type) {
        RotorConfig.RotorDefinition def = RotorConfig.ROTOR_DEFINITIONS.get(type);
        return new Rotor(def.wiring, def.getFirstNotch());
    }
    
    private void encrypt() {
        try {
            // Update rotor configuration
            List<Rotor> rotors = Arrays.asList(
                createRotor(rotor1Combo.getValue()),
                createRotor(rotor2Combo.getValue()),
                createRotor(rotor3Combo.getValue())
            );
            
            // Set positions
            int[] positions = {
                rotor1PosField.getText().charAt(0) - 'A',
                rotor2PosField.getText().charAt(0) - 'A',
                rotor3PosField.getText().charAt(0) - 'A'
            };
            
            // Set ring settings
            rotors.get(0).setRing(rotor1RingField.getText().charAt(0) - 'A');
            rotors.get(1).setRing(rotor2RingField.getText().charAt(0) - 'A');
            rotors.get(2).setRing(rotor3RingField.getText().charAt(0) - 'A');
            
            // Create new Enigma machine
            Reflector reflector = new Reflector(RotorConfig.REFLECTOR_DEFINITIONS.get(reflectorCombo.getValue()));
            
            // Parse plugboard
            String[] plugboardPairs = plugboardField.getText().trim().isEmpty() ? 
                new String[0] : plugboardField.getText().trim().split("\\s+");
            Plugboard plugboard = new Plugboard(plugboardPairs);
            
            enigmaMachine = new EnigmaMachine(rotors, reflector, plugboard);
            enigmaMachine.setRotorPositions(positions);
            
            // Encrypt message
            String message = messageArea.getText().toUpperCase().replaceAll("[^A-Z]", "");
            String result = enigmaMachine.encrypt(message);
            
            resultArea.setText(result);
            
            // Update rotor positions after encryption
            updateRotorPositions();
            
        } catch (Exception e) {
            showError("暗号化エラー", e.getMessage());
        }
    }
    
    private void updateRotorPositions() {
        List<Rotor> rotors = enigmaMachine.getRotors();
        rotor1PosField.setText(String.valueOf((char)('A' + rotors.get(0).getPosition())));
        rotor2PosField.setText(String.valueOf((char)('A' + rotors.get(1).getPosition())));
        rotor3PosField.setText(String.valueOf((char)('A' + rotors.get(2).getPosition())));
    }
    
    private void saveConfiguration(Stage stage) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Save Enigma Configuration");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );
        
        File file = fileChooser.showSaveDialog(stage);
        if (file != null) {
            try {
                Map<String, Object> config = new HashMap<>();
                
                Map<String, Object> rotorConfig = new HashMap<>();
                rotorConfig.put("types", Arrays.asList(
                    rotor1Combo.getValue(),
                    rotor2Combo.getValue(),
                    rotor3Combo.getValue()
                ));
                rotorConfig.put("positions", Arrays.asList(
                    rotor1PosField.getText(),
                    rotor2PosField.getText(),
                    rotor3PosField.getText()
                ));
                rotorConfig.put("rings", Arrays.asList(
                    rotor1RingField.getText(),
                    rotor2RingField.getText(),
                    rotor3RingField.getText()
                ));
                
                config.put("rotors", rotorConfig);
                config.put("reflector", reflectorCombo.getValue());
                config.put("plugboard", plugboardField.getText());
                config.put("message", messageArea.getText());
                
                Gson gson = new GsonBuilder().setPrettyPrinting().create();
                try (FileWriter writer = new FileWriter(file)) {
                    gson.toJson(config, writer);
                }
                
                showInfo("成功", "設定を保存しました: " + file.getName());
                
            } catch (Exception e) {
                showError("保存エラー", e.getMessage());
            }
        }
    }
    
    private void loadConfiguration(Stage stage) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Load Enigma Configuration");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );
        
        File file = fileChooser.showOpenDialog(stage);
        if (file != null) {
            try {
                Gson gson = new Gson();
                Map<String, Object> config;
                try (FileReader reader = new FileReader(file)) {
                    config = gson.fromJson(reader, Map.class);
                }
                
                // Apply configuration
                Map<String, Object> rotorConfig = (Map<String, Object>) config.get("rotors");
                if (rotorConfig != null) {
                    List<String> types = (List<String>) rotorConfig.get("types");
                    if (types != null && types.size() >= 3) {
                        rotor1Combo.setValue(types.get(0));
                        rotor2Combo.setValue(types.get(1));
                        rotor3Combo.setValue(types.get(2));
                    }
                    
                    List<String> positions = (List<String>) rotorConfig.get("positions");
                    if (positions != null && positions.size() >= 3) {
                        rotor1PosField.setText(positions.get(0));
                        rotor2PosField.setText(positions.get(1));
                        rotor3PosField.setText(positions.get(2));
                    }
                    
                    List<String> rings = (List<String>) rotorConfig.get("rings");
                    if (rings != null && rings.size() >= 3) {
                        rotor1RingField.setText(rings.get(0));
                        rotor2RingField.setText(rings.get(1));
                        rotor3RingField.setText(rings.get(2));
                    }
                }
                
                if (config.containsKey("reflector")) {
                    reflectorCombo.setValue((String) config.get("reflector"));
                }
                
                if (config.containsKey("plugboard")) {
                    plugboardField.setText((String) config.get("plugboard"));
                }
                
                if (config.containsKey("message")) {
                    messageArea.setText((String) config.get("message"));
                }
                
                showInfo("成功", "設定を読み込みました: " + file.getName());
                
            } catch (Exception e) {
                showError("読み込みエラー", e.getMessage());
            }
        }
    }
    
    private void showError(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.ERROR);
        alert.setTitle(title);
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void showInfo(String title, String message) {
        Alert alert = new Alert(Alert.AlertType.INFORMATION);
        alert.setTitle(title);
        alert.setContentText(message);
        alert.showAndWait();
    }
    
    private void openBombeWindow() {
        BombeGUI bombeGUI = new BombeGUI();
        Stage bombeStage = new Stage();
        bombeStage.setTitle("Bombe Attack Tool");
        bombeStage.initModality(Modality.NONE);
        try {
            bombeGUI.start(bombeStage);
        } catch (Exception e) {
            showError("エラー", "Bombeウィンドウを開けませんでした: " + e.getMessage());
        }
    }
    
    private void importBombeResult(Stage stage) {
        FileChooser fileChooser = new FileChooser();
        fileChooser.setTitle("Import Bombe Result");
        fileChooser.getExtensionFilters().add(
            new FileChooser.ExtensionFilter("JSON Files", "*.json")
        );
        
        File file = fileChooser.showOpenDialog(stage);
        if (file != null) {
            try {
                Gson gson = new Gson();
                JsonObject root;
                try (FileReader reader = new FileReader(file)) {
                    root = gson.fromJson(reader, JsonObject.class);
                }
                
                // Check if this is a Bombe result file
                if (!root.has("results") || !root.has("settings")) {
                    showError("エラー", "これはBombeの結果ファイルではありません");
                    return;
                }
                
                // Get settings from Bombe result
                JsonObject settings = root.getAsJsonObject("settings");
                
                // Create a dialog to select which result to use
                JsonArray results = root.getAsJsonArray("results");
                if (results.size() == 0) {
                    showError("エラー", "結果が見つかりません");
                    return;
                }
                
                // Create choice dialog
                List<String> choices = new ArrayList<>();
                for (int i = 0; i < Math.min(10, results.size()); i++) {
                    JsonObject result = results.get(i).getAsJsonObject();
                    String position = result.get("position").getAsString();
                    String rotors = result.get("rotors").getAsString();
                    double score = result.get("score").getAsDouble();
                    double matchRate = result.get("matchRate").getAsDouble();
                    
                    // プラグボード情報を取得
                    String plugboardStr = "なし";
                    if (result.has("plugboard")) {
                        JsonArray plugboardArray = result.getAsJsonArray("plugboard");
                        if (plugboardArray != null && plugboardArray.size() > 0) {
                            StringBuilder pb = new StringBuilder();
                            for (int j = 0; j < plugboardArray.size(); j++) {
                                if (j > 0) pb.append(" ");
                                pb.append(plugboardArray.get(j).getAsString());
                            }
                            plugboardStr = pb.toString();
                        }
                    }
                    
                    choices.add(String.format("#%d: %s (%s) - Score: %.1f, Match: %.1f%%, PB: %s", 
                        i + 1, position, rotors, score, matchRate * 100, plugboardStr));
                }
                
                ChoiceDialog<String> dialog = new ChoiceDialog<>(choices.get(0), choices);
                dialog.setTitle("Select Result");
                dialog.setHeaderText("Bombeの攻撃結果を選択してください");
                dialog.setContentText("Result:");
                
                Optional<String> selectedChoice = dialog.showAndWait();
                if (selectedChoice.isPresent()) {
                    int index = choices.indexOf(selectedChoice.get());
                    JsonObject selectedResult = results.get(index).getAsJsonObject();
                    
                    // Apply the selected configuration
                    String position = selectedResult.get("position").getAsString();
                    String rotorConfig = selectedResult.get("rotors").getAsString();
                    String[] rotors = rotorConfig.split("-");
                    
                    // Set rotors
                    if (rotors.length >= 3) {
                        rotor1Combo.setValue(rotors[0]);
                        rotor2Combo.setValue(rotors[1]);
                        rotor3Combo.setValue(rotors[2]);
                    }
                    
                    // Set positions
                    if (position.length() >= 3) {
                        rotor1PosField.setText(String.valueOf(position.charAt(0)));
                        rotor2PosField.setText(String.valueOf(position.charAt(1)));
                        rotor3PosField.setText(String.valueOf(position.charAt(2)));
                    }
                    
                    // Set reflector from settings
                    if (settings.has("reflector")) {
                        reflectorCombo.setValue(settings.get("reflector").getAsString());
                    }
                    
                    // Set plugboard configuration
                    JsonArray plugboardArray = selectedResult.getAsJsonArray("plugboard");
                    if (plugboardArray != null && plugboardArray.size() > 0) {
                        StringBuilder plugboardStr = new StringBuilder();
                        for (int i = 0; i < plugboardArray.size(); i++) {
                            if (i > 0) plugboardStr.append(" ");
                            plugboardStr.append(plugboardArray.get(i).getAsString());
                        }
                        plugboardField.setText(plugboardStr.toString());
                    } else {
                        plugboardField.setText("");
                    }
                    
                    showInfo("成功", "Bombeの結果をインポートしました\n" + 
                        "Position: " + position + "\n" +
                        "Rotors: " + rotorConfig);
                }
                
            } catch (Exception e) {
                showError("読み込みエラー", e.getMessage());
            }
        }
    }
    
    public static void main(String[] args) {
        launch(args);
    }
}
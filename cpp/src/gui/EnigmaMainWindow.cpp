#include "EnigmaMainWindow.h"
#include "BombeWindow.h"
#include "../core/EnigmaMachine.h"
#include "../core/Rotor.h"
#include "../core/Reflector.h"
#include "../core/Plugboard.h"
#include "../core/RotorConfig.h"

#include <sstream>
#include <algorithm>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QGroupBox>
#include <QLabel>
#include <QComboBox>
#include <QLineEdit>
#include <QTextEdit>
#include <QPushButton>
#include <QFileDialog>
#include <QMessageBox>
#include <QInputDialog>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QTextStream>
#include <QRegularExpressionValidator>

EnigmaMainWindow::EnigmaMainWindow(QWidget *parent)
    : QMainWindow(parent) {
    setupUi();
    setupEnigmaMachine();
    
    setWindowTitle("Enigma Machine Simulator - Qt Edition");
    resize(800, 700);
}

EnigmaMainWindow::~EnigmaMainWindow() = default;

void EnigmaMainWindow::setupUi() {
    auto* centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    auto* mainLayout = new QVBoxLayout(centralWidget);
    
    // Title
    auto* titleLabel = new QLabel("Enigma Machine Simulator", this);
    titleLabel->setAlignment(Qt::AlignCenter);
    titleLabel->setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;");
    mainLayout->addWidget(titleLabel);
    
    // Rotor Configuration
    auto* rotorGroup = new QGroupBox("Rotor Configuration", this);
    auto* rotorLayout = new QGridLayout(rotorGroup);
    
    // Headers
    rotorLayout->addWidget(new QLabel("Position"), 0, 0);
    rotorLayout->addWidget(new QLabel("Rotor"), 0, 1);
    rotorLayout->addWidget(new QLabel("Position"), 0, 2);
    rotorLayout->addWidget(new QLabel("Ring"), 0, 3);
    
    // Rotor 1 (Right)
    rotorLayout->addWidget(new QLabel("Right:"), 1, 0);
    rotor1TypeCombo = new QComboBox(this);
    rotor1TypeCombo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotorLayout->addWidget(rotor1TypeCombo, 1, 1);
    
    rotor1PosEdit = new QLineEdit("A", this);
    rotor1PosEdit->setMaxLength(1);
    rotor1PosEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor1PosEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor1PosEdit, 1, 2);
    
    rotor1RingEdit = new QLineEdit("A", this);
    rotor1RingEdit->setMaxLength(1);
    rotor1RingEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor1RingEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor1RingEdit, 1, 3);
    
    // Rotor 2 (Middle)
    rotorLayout->addWidget(new QLabel("Middle:"), 2, 0);
    rotor2TypeCombo = new QComboBox(this);
    rotor2TypeCombo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotor2TypeCombo->setCurrentIndex(1); // II
    rotorLayout->addWidget(rotor2TypeCombo, 2, 1);
    
    rotor2PosEdit = new QLineEdit("A", this);
    rotor2PosEdit->setMaxLength(1);
    rotor2PosEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor2PosEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor2PosEdit, 2, 2);
    
    rotor2RingEdit = new QLineEdit("A", this);
    rotor2RingEdit->setMaxLength(1);
    rotor2RingEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor2RingEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor2RingEdit, 2, 3);
    
    // Rotor 3 (Left)
    rotorLayout->addWidget(new QLabel("Left:"), 3, 0);
    rotor3TypeCombo = new QComboBox(this);
    rotor3TypeCombo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotor3TypeCombo->setCurrentIndex(2); // III
    rotorLayout->addWidget(rotor3TypeCombo, 3, 1);
    
    rotor3PosEdit = new QLineEdit("A", this);
    rotor3PosEdit->setMaxLength(1);
    rotor3PosEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor3PosEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor3PosEdit, 3, 2);
    
    rotor3RingEdit = new QLineEdit("A", this);
    rotor3RingEdit->setMaxLength(1);
    rotor3RingEdit->setValidator(new QRegularExpressionValidator(QRegularExpression("[A-Z]"), this));
    rotor3RingEdit->setMaximumWidth(50);
    rotorLayout->addWidget(rotor3RingEdit, 3, 3);
    
    // Reflector
    rotorLayout->addWidget(new QLabel("Reflector:"), 4, 0);
    reflectorCombo = new QComboBox(this);
    reflectorCombo->addItems({"B", "C"});
    rotorLayout->addWidget(reflectorCombo, 4, 1);
    
    mainLayout->addWidget(rotorGroup);
    
    // Plugboard
    auto* plugboardLayout = new QHBoxLayout();
    plugboardLayout->addWidget(new QLabel("Plugboard:"));
    plugboardEdit = new QLineEdit(this);
    plugboardEdit->setPlaceholderText("例: AB CD EF (空欄でプラグボードなし、最大10組)");
    plugboardLayout->addWidget(plugboardEdit);
    mainLayout->addLayout(plugboardLayout);
    
    // Input/Output
    auto* ioGroup = new QGroupBox("Message", this);
    auto* ioLayout = new QVBoxLayout(ioGroup);
    
    ioLayout->addWidget(new QLabel("Input:"));
    inputTextEdit = new QTextEdit(this);
    inputTextEdit->setMaximumHeight(100);
    inputTextEdit->setPlaceholderText("暗号化するメッセージを入力...");
    ioLayout->addWidget(inputTextEdit);
    
    ioLayout->addWidget(new QLabel("Output:"));
    outputTextEdit = new QTextEdit(this);
    outputTextEdit->setMaximumHeight(100);
    outputTextEdit->setReadOnly(true);
    outputTextEdit->setStyleSheet("font-family: monospace;");
    ioLayout->addWidget(outputTextEdit);
    
    mainLayout->addWidget(ioGroup);
    
    // Buttons
    auto* buttonLayout = new QHBoxLayout();
    
    encryptButton = new QPushButton("Encrypt", this);
    saveConfigButton = new QPushButton("Save Config", this);
    loadConfigButton = new QPushButton("Load Config", this);
    importBombeButton = new QPushButton("Import Bombe Result", this);
    openBombeButton = new QPushButton("Open Bombe", this);
    
    buttonLayout->addWidget(encryptButton);
    buttonLayout->addWidget(saveConfigButton);
    buttonLayout->addWidget(loadConfigButton);
    buttonLayout->addWidget(importBombeButton);
    buttonLayout->addWidget(openBombeButton);
    
    mainLayout->addLayout(buttonLayout);
    
    // Connect signals
    connect(encryptButton, &QPushButton::clicked, this, &EnigmaMainWindow::onEncryptClicked);
    connect(saveConfigButton, &QPushButton::clicked, this, &EnigmaMainWindow::onSaveConfigClicked);
    connect(loadConfigButton, &QPushButton::clicked, this, &EnigmaMainWindow::onLoadConfigClicked);
    connect(importBombeButton, &QPushButton::clicked, this, &EnigmaMainWindow::onImportBombeResultClicked);
    connect(openBombeButton, &QPushButton::clicked, this, &EnigmaMainWindow::onOpenBombeClicked);
}

void EnigmaMainWindow::setupEnigmaMachine() {
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    
    // Create rotors with default configuration
    auto& r1Def = enigma::ROTOR_DEFINITIONS.at("I");
    rotors.push_back(std::make_unique<Rotor>(r1Def.wiring, r1Def.getFirstNotch()));
    
    auto& r2Def = enigma::ROTOR_DEFINITIONS.at("II");
    rotors.push_back(std::make_unique<Rotor>(r2Def.wiring, r2Def.getFirstNotch()));
    
    auto& r3Def = enigma::ROTOR_DEFINITIONS.at("III");
    rotors.push_back(std::make_unique<Rotor>(r3Def.wiring, r3Def.getFirstNotch()));
    
    // Create reflector
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at("B");
    auto reflector = std::make_unique<Reflector>(refDef.wiring);
    
    // Create plugboard
    auto plugboard = std::make_unique<Plugboard>();
    
    // Create Enigma machine
    enigmaMachine = std::make_unique<EnigmaMachine>(
        std::move(rotors), 
        std::move(reflector), 
        std::move(plugboard)
    );
}

void EnigmaMainWindow::updateEnigmaFromUi() {
    // Recreate machine with current settings
    auto rotors = std::vector<std::unique_ptr<Rotor>>();
    
    // Create rotors
    std::string rotor1Type = rotor1TypeCombo->currentText().toStdString();
    std::string rotor2Type = rotor2TypeCombo->currentText().toStdString();
    std::string rotor3Type = rotor3TypeCombo->currentText().toStdString();
    
    auto& r1Def = enigma::ROTOR_DEFINITIONS.at(rotor1Type);
    auto rotor1 = std::make_unique<Rotor>(r1Def.wiring, r1Def.getFirstNotch());
    rotor1->setRing(rotor1RingEdit->text().isEmpty() ? 0 : rotor1RingEdit->text()[0].toLatin1() - 'A');
    rotors.push_back(std::move(rotor1));
    
    auto& r2Def = enigma::ROTOR_DEFINITIONS.at(rotor2Type);
    auto rotor2 = std::make_unique<Rotor>(r2Def.wiring, r2Def.getFirstNotch());
    rotor2->setRing(rotor2RingEdit->text().isEmpty() ? 0 : rotor2RingEdit->text()[0].toLatin1() - 'A');
    rotors.push_back(std::move(rotor2));
    
    auto& r3Def = enigma::ROTOR_DEFINITIONS.at(rotor3Type);
    auto rotor3 = std::make_unique<Rotor>(r3Def.wiring, r3Def.getFirstNotch());
    rotor3->setRing(rotor3RingEdit->text().isEmpty() ? 0 : rotor3RingEdit->text()[0].toLatin1() - 'A');
    rotors.push_back(std::move(rotor3));
    
    // Create reflector
    std::string reflectorType = reflectorCombo->currentText().toStdString();
    auto& refDef = enigma::REFLECTOR_DEFINITIONS.at(reflectorType);
    auto reflector = std::make_unique<Reflector>(refDef.wiring);
    
    // Create plugboard
    auto plugboard = std::make_unique<Plugboard>();
    setPlugboardFromString(plugboardEdit->text().toStdString());
    
    // Parse plugboard pairs
    std::vector<std::string> pairs;
    std::string pbText = plugboardEdit->text().toStdString();
    std::istringstream iss(pbText);
    std::string pair;
    while (iss >> pair) {
        if (pair.length() == 2) {
            pairs.push_back(pair);
        }
    }
    plugboard = std::make_unique<Plugboard>(pairs);
    
    // Create Enigma machine
    enigmaMachine = std::make_unique<EnigmaMachine>(
        std::move(rotors), 
        std::move(reflector), 
        std::move(plugboard)
    );
    
    // Set positions
    std::vector<int> positions = {
        rotor1PosEdit->text().isEmpty() ? 0 : rotor1PosEdit->text()[0].toLatin1() - 'A',
        rotor2PosEdit->text().isEmpty() ? 0 : rotor2PosEdit->text()[0].toLatin1() - 'A',
        rotor3PosEdit->text().isEmpty() ? 0 : rotor3PosEdit->text()[0].toLatin1() - 'A'
    };
    enigmaMachine->setRotorPositions(positions);
}

void EnigmaMainWindow::onEncryptClicked() {
    updateEnigmaFromUi();
    
    std::string input = inputTextEdit->toPlainText().toStdString();
    std::string output = enigmaMachine->encrypt(input);
    
    outputTextEdit->setPlainText(QString::fromStdString(output));
    
    // Update rotor positions in the UI after encryption
    updateRotorPositions();
}

void EnigmaMainWindow::onSaveConfigClicked() {
    QString fileName = QFileDialog::getSaveFileName(this, 
        "Save Enigma Configuration", "", "JSON Files (*.json)");
    
    if (fileName.isEmpty()) return;
    
    QJsonObject config;
    QJsonObject rotorConfig;
    
    // Rotor types
    QJsonArray types;
    types.append(rotor1TypeCombo->currentText());
    types.append(rotor2TypeCombo->currentText());
    types.append(rotor3TypeCombo->currentText());
    rotorConfig["types"] = types;
    
    // Rotor positions
    QJsonArray positions;
    positions.append(rotor1PosEdit->text());
    positions.append(rotor2PosEdit->text());
    positions.append(rotor3PosEdit->text());
    rotorConfig["positions"] = positions;
    
    // Ring settings
    QJsonArray rings;
    rings.append(rotor1RingEdit->text());
    rings.append(rotor2RingEdit->text());
    rings.append(rotor3RingEdit->text());
    rotorConfig["rings"] = rings;
    
    config["rotors"] = rotorConfig;
    config["reflector"] = reflectorCombo->currentText();
    config["plugboard"] = plugboardEdit->text();
    config["message"] = inputTextEdit->toPlainText();
    
    QJsonDocument doc(config);
    QFile file(fileName);
    if (file.open(QIODevice::WriteOnly)) {
        file.write(doc.toJson());
        file.close();
        QMessageBox::information(this, "Success", "Configuration saved successfully!");
    } else {
        QMessageBox::warning(this, "Error", "Failed to save configuration!");
    }
}

void EnigmaMainWindow::onLoadConfigClicked() {
    QString fileName = QFileDialog::getOpenFileName(this, 
        "Load Enigma Configuration", "", "JSON Files (*.json)");
    
    if (fileName.isEmpty()) return;
    
    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly)) {
        QMessageBox::warning(this, "Error", "Failed to open file!");
        return;
    }
    
    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();
    
    QJsonObject config = doc.object();
    
    // Load rotors
    if (config.contains("rotors")) {
        QJsonObject rotorConfig = config["rotors"].toObject();
        
        if (rotorConfig.contains("types")) {
            QJsonArray types = rotorConfig["types"].toArray();
            if (types.size() >= 3) {
                rotor1TypeCombo->setCurrentText(types[0].toString());
                rotor2TypeCombo->setCurrentText(types[1].toString());
                rotor3TypeCombo->setCurrentText(types[2].toString());
            }
        }
        
        if (rotorConfig.contains("positions")) {
            QJsonArray positions = rotorConfig["positions"].toArray();
            if (positions.size() >= 3) {
                rotor1PosEdit->setText(positions[0].toString());
                rotor2PosEdit->setText(positions[1].toString());
                rotor3PosEdit->setText(positions[2].toString());
            }
        }
        
        if (rotorConfig.contains("rings")) {
            QJsonArray rings = rotorConfig["rings"].toArray();
            if (rings.size() >= 3) {
                rotor1RingEdit->setText(rings[0].toString());
                rotor2RingEdit->setText(rings[1].toString());
                rotor3RingEdit->setText(rings[2].toString());
            }
        }
    }
    
    if (config.contains("reflector")) {
        reflectorCombo->setCurrentText(config["reflector"].toString());
    }
    
    if (config.contains("plugboard")) {
        plugboardEdit->setText(config["plugboard"].toString());
    }
    
    if (config.contains("message")) {
        inputTextEdit->setPlainText(config["message"].toString());
    }
    
    QMessageBox::information(this, "Success", "Configuration loaded successfully!");
}

void EnigmaMainWindow::onImportBombeResultClicked() {
    QString fileName = QFileDialog::getOpenFileName(this, 
        "Import Bombe Result", "", "JSON Files (*.json)");
    
    if (fileName.isEmpty()) return;
    
    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly)) {
        QMessageBox::warning(this, "Error", "Failed to open file!");
        return;
    }
    
    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();
    
    QJsonObject root = doc.object();
    
    // Check if this is a Bombe result file
    if (!root.contains("results") || !root.contains("settings")) {
        QMessageBox::warning(this, "Error", "This is not a valid Bombe result file!");
        return;
    }
    
    QJsonArray results = root["results"].toArray();
    if (results.isEmpty()) {
        QMessageBox::warning(this, "Error", "No results found in file!");
        return;
    }
    
    // Build list of results for selection
    QStringList items;
    for (int i = 0; i < std::min(10, static_cast<int>(results.size())); ++i) {
        QJsonObject result = results[i].toObject();
        
        // プラグボード情報を取得
        QString plugboardStr = "なし";
        if (result.contains("plugboard")) {
            QJsonArray plugboardArray = result["plugboard"].toArray();
            if (!plugboardArray.isEmpty()) {
                QStringList pairs;
                for (const auto& value : plugboardArray) {
                    pairs << value.toString();
                }
                plugboardStr = pairs.join(" ");
            }
        }
        
        QString item = QString("#%1: %2 (%3) - Score: %4, Match: %5%, PB: %6")
            .arg(i + 1)
            .arg(result["position"].toString())
            .arg(result["rotors"].toString())
            .arg(result["score"].toDouble(), 0, 'f', 1)
            .arg(result["matchRate"].toDouble() * 100, 0, 'f', 1)
            .arg(plugboardStr);
        items << item;
    }
    
    bool ok;
    QString selected = QInputDialog::getItem(this, "Select Result", 
        "Select a Bombe result to apply:", items, 0, false, &ok);
    
    if (!ok || selected.isEmpty()) return;
    
    int index = items.indexOf(selected);
    if (index < 0 || index >= results.size()) return;
    
    QJsonObject selectedResult = results[index].toObject();
    QJsonObject settings = root["settings"].toObject();
    
    // Apply rotor configuration
    QString rotorConfig = selectedResult["rotors"].toString();
    QStringList rotors = rotorConfig.split("-");
    if (rotors.size() >= 3) {
        rotor1TypeCombo->setCurrentText(rotors[0]);
        rotor2TypeCombo->setCurrentText(rotors[1]);
        rotor3TypeCombo->setCurrentText(rotors[2]);
    }
    
    // Apply positions
    QString positions = selectedResult["position"].toString();
    if (positions.length() >= 3) {
        rotor1PosEdit->setText(QString(positions[0]));
        rotor2PosEdit->setText(QString(positions[1]));
        rotor3PosEdit->setText(QString(positions[2]));
    }
    
    // Apply reflector
    if (settings.contains("reflector")) {
        reflectorCombo->setCurrentText(settings["reflector"].toString());
    }
    
    // Apply plugboard
    QJsonArray plugboardArray = selectedResult["plugboard"].toArray();
    QString plugboardStr;
    for (const auto& value : plugboardArray) {
        if (!plugboardStr.isEmpty()) plugboardStr += " ";
        plugboardStr += value.toString();
    }
    plugboardEdit->setText(plugboardStr);
    
    QMessageBox::information(this, "Success", 
        QString("Bombe result applied!\nPosition: %1\nRotors: %2")
            .arg(positions)
            .arg(rotorConfig));
}

void EnigmaMainWindow::onOpenBombeClicked() {
    // Open Bombe window
    BombeWindow* bombeWindow = new BombeWindow(this);
    bombeWindow->setAttribute(Qt::WA_DeleteOnClose);
    bombeWindow->show();
}

void EnigmaMainWindow::updateRotorPositions() {
    // Get current rotor positions from the Enigma machine
    std::vector<int> positions = enigmaMachine->getRotorPositions();
    
    // Update the UI with the new positions
    if (positions.size() >= 3) {
        rotor1PosEdit->setText(QString(QChar('A' + positions[0])));
        rotor2PosEdit->setText(QString(QChar('A' + positions[1])));
        rotor3PosEdit->setText(QString(QChar('A' + positions[2])));
    }
}

std::string EnigmaMainWindow::getPlugboardString() const {
    return plugboardEdit->text().toStdString();
}

void EnigmaMainWindow::setPlugboardFromString(const std::string& str) {
    plugboardEdit->setText(QString::fromStdString(str));
}
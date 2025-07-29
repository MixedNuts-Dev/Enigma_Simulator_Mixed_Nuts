#include "BombeWindow.h"
#include "../core/EnigmaMachine.h"
#include "../core/Rotor.h"
#include "../core/Reflector.h"
#include "../core/Plugboard.h"
#include "../core/RotorConfig.h"
#include "../core/BombeAttack.h"

#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QGroupBox>
#include <QLabel>
#include <QLineEdit>
#include <QTextEdit>
#include <QComboBox>
#include <QCheckBox>
#include <QPushButton>
#include <QProgressBar>
#include <QListWidget>
#include <QFileDialog>
#include <QMessageBox>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QFile>
#include <QSettings>
#include <QRegularExpression>

#include <algorithm>
#include <thread>
#include <chrono>

BombeWindow::BombeWindow(QWidget *parent)
    : QMainWindow(parent), workerThread(nullptr), worker(nullptr) {
    setupUi();
    setWindowTitle("Bombe Machine Simulator - Qt Edition");
    resize(800, 900);
}

BombeWindow::~BombeWindow() {
    if (workerThread) {
        workerThread->quit();
        workerThread->wait();
        delete workerThread;
        delete worker;
    }
}

void BombeWindow::setupUi() {
    auto* centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    auto* mainLayout = new QVBoxLayout(centralWidget);
    
    // Title
    auto* titleLabel = new QLabel("Bombe Machine Simulator", this);
    titleLabel->setAlignment(Qt::AlignCenter);
    titleLabel->setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px;");
    mainLayout->addWidget(titleLabel);
    
    auto* descLabel = new QLabel("Electro-mechanical device used by British codebreakers\nduring WWII to help decipher German Enigma-encrypted messages.", this);
    descLabel->setAlignment(Qt::AlignCenter);
    mainLayout->addWidget(descLabel);
    
    // Input section
    auto* inputGroup = new QGroupBox("Input Configuration", this);
    auto* inputLayout = new QGridLayout(inputGroup);
    
    inputLayout->addWidget(new QLabel("Crib (既知の平文):"), 0, 0);
    cribEdit = new QLineEdit("HELLOWORLD", this);
    inputLayout->addWidget(cribEdit, 0, 1);
    
    inputLayout->addWidget(new QLabel("Cipher (暗号文):"), 1, 0);
    cipherEdit = new QLineEdit("MFNCZBBFZM", this);
    inputLayout->addWidget(cipherEdit, 1, 1);
    
    mainLayout->addWidget(inputGroup);
    
    // Rotor configuration
    auto* rotorGroup = new QGroupBox("Rotor Configuration", this);
    auto* rotorLayout = new QHBoxLayout(rotorGroup);
    
    rotorLayout->addWidget(new QLabel("Rotors:"));
    
    rotor1Combo = new QComboBox(this);
    rotor1Combo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotorLayout->addWidget(rotor1Combo);
    
    rotor2Combo = new QComboBox(this);
    rotor2Combo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotor2Combo->setCurrentIndex(1);
    rotorLayout->addWidget(rotor2Combo);
    
    rotor3Combo = new QComboBox(this);
    rotor3Combo->addItems({"I", "II", "III", "IV", "V", "VI", "VII", "VIII"});
    rotor3Combo->setCurrentIndex(2);
    rotorLayout->addWidget(rotor3Combo);
    
    rotorLayout->addWidget(new QLabel("Reflector:"));
    reflectorCombo = new QComboBox(this);
    reflectorCombo->addItems({"B", "C"});
    rotorLayout->addWidget(reflectorCombo);
    
    mainLayout->addWidget(rotorGroup);
    
    testAllOrdersCheck = new QCheckBox("Test all rotor orders (全ローター順を試す)", this);
    mainLayout->addWidget(testAllOrdersCheck);
    
    searchWithoutPlugboardCheck = new QCheckBox("Search without plugboard (プラグボードなしで検索)", this);
    mainLayout->addWidget(searchWithoutPlugboardCheck);
    
    // Control buttons
    auto* buttonLayout = new QHBoxLayout();
    
    startButton = new QPushButton("Start Attack", this);
    stopButton = new QPushButton("Stop", this);
    stopButton->setEnabled(false);
    clearButton = new QPushButton("Clear Log", this);
    saveSettingsButton = new QPushButton("Save Settings", this);
    loadSettingsButton = new QPushButton("Load Settings", this);
    exportButton = new QPushButton("Export Results", this);
    exportButton->setEnabled(false);
    
    buttonLayout->addWidget(startButton);
    buttonLayout->addWidget(stopButton);
    buttonLayout->addWidget(clearButton);
    buttonLayout->addWidget(saveSettingsButton);
    buttonLayout->addWidget(loadSettingsButton);
    buttonLayout->addWidget(exportButton);
    
    mainLayout->addLayout(buttonLayout);
    
    // Progress
    progressBar = new QProgressBar(this);
    progressBar->setVisible(false);
    mainLayout->addWidget(progressBar);
    
    // Log
    auto* logGroup = new QGroupBox("Analysis Log", this);
    auto* logLayout = new QVBoxLayout(logGroup);
    
    logEdit = new QTextEdit(this);
    logEdit->setReadOnly(true);
    logEdit->setMaximumHeight(200);
    logEdit->setStyleSheet("font-family: monospace;");
    logLayout->addWidget(logEdit);
    
    mainLayout->addWidget(logGroup);
    
    // Results
    auto* resultsGroup = new QGroupBox("Results", this);
    auto* resultsLayout = new QVBoxLayout(resultsGroup);
    
    resultLabel = new QLabel("No results yet", this);
    resultsLayout->addWidget(resultLabel);
    
    resultsList = new QListWidget(this);
    resultsLayout->addWidget(resultsList);
    
    mainLayout->addWidget(resultsGroup);
    
    // Connect signals
    connect(startButton, &QPushButton::clicked, this, &BombeWindow::onStartAttackClicked);
    connect(stopButton, &QPushButton::clicked, this, &BombeWindow::onStopAttackClicked);
    connect(clearButton, &QPushButton::clicked, this, &BombeWindow::onClearLogClicked);
    connect(saveSettingsButton, &QPushButton::clicked, this, &BombeWindow::onSaveSettingsClicked);
    connect(loadSettingsButton, &QPushButton::clicked, this, &BombeWindow::onLoadSettingsClicked);
    connect(exportButton, &QPushButton::clicked, this, &BombeWindow::onExportResultsClicked);
    connect(resultsList, &QListWidget::itemSelectionChanged, this, &BombeWindow::onResultSelected);
}

void BombeWindow::onStartAttackClicked() {
    QString crib = cribEdit->text().toUpper();
    QString cipher = cipherEdit->text().toUpper();
    
    // Remove non-alphabetic characters
    crib.remove(QRegularExpression("[^A-Z]"));
    cipher.remove(QRegularExpression("[^A-Z]"));
    
    if (crib.isEmpty() || cipher.isEmpty()) {
        QMessageBox::warning(this, "Error", "Please enter both crib and cipher text");
        return;
    }
    
    if (crib.length() != cipher.length()) {
        QMessageBox::warning(this, "Error", "Crib and cipher must be the same length");
        return;
    }
    
    // Setup UI for attack
    startButton->setEnabled(false);
    stopButton->setEnabled(true);
    exportButton->setEnabled(false);
    progressBar->setVisible(true);
    progressBar->setRange(0, 0); // Indeterminate
    resultsList->clear();
    allResults.clear();
    
    // Create worker thread
    if (!workerThread) {
        workerThread = new QThread();
        worker = new BombeWorker();
        worker->moveToThread(workerThread);
        
        connect(this, &BombeWindow::startAttack, worker, &BombeWorker::doAttack);
        connect(worker, &BombeWorker::progress, this, &BombeWindow::onAttackProgress);
        connect(worker, &BombeWorker::finished, this, &BombeWindow::onAttackFinished);
        connect(worker, &BombeWorker::error, this, &BombeWindow::onAttackError);
        
        workerThread->start();
    }
    
    // Start attack
    QStringList rotors;
    if (testAllOrdersCheck->isChecked()) {
        // Test all rotor ordersがチェックされている場合、すべてのローターを渡す
        rotors << "I" << "II" << "III" << "IV" << "V" << "VI" << "VII" << "VIII";
    } else {
        // 選択されたローターのみを使用
        rotors << rotor1Combo->currentText()
               << rotor2Combo->currentText()
               << rotor3Combo->currentText();
    }
    
    emit startAttack(crib, cipher, rotors, reflectorCombo->currentText(), 
                     testAllOrdersCheck->isChecked(), searchWithoutPlugboardCheck->isChecked());
}

void BombeWindow::onStopAttackClicked() {
    if (worker) {
        worker->stop();
    }
    logEdit->append("ユーザーにより攻撃が停止されました");
}

void BombeWindow::onClearLogClicked() {
    logEdit->clear();
    resultsList->clear();
    resultLabel->setText("No results yet");
}

void BombeWindow::onSaveSettingsClicked() {
    QSettings settings("EnigmaProject", "BombeSimulator");
    settings.setValue("crib", cribEdit->text());
    settings.setValue("cipher", cipherEdit->text());
    settings.setValue("rotor1", rotor1Combo->currentText());
    settings.setValue("rotor2", rotor2Combo->currentText());
    settings.setValue("rotor3", rotor3Combo->currentText());
    settings.setValue("reflector", reflectorCombo->currentText());
    settings.setValue("testAllOrders", testAllOrdersCheck->isChecked());
    settings.setValue("searchWithoutPlugboard", searchWithoutPlugboardCheck->isChecked());
    
    QMessageBox::information(this, "Success", "設定が保存されました");
}

void BombeWindow::onLoadSettingsClicked() {
    QString fileName = QFileDialog::getOpenFileName(this, 
        "Load Settings", "", "JSON Files (*.json)");
    
    if (fileName.isEmpty()) return;
    
    QFile file(fileName);
    if (!file.open(QIODevice::ReadOnly)) {
        QMessageBox::warning(this, "Error", "Failed to open file!");
        return;
    }
    
    QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
    file.close();
    
    QJsonObject settings = doc.object();
    
    if (settings.contains("crib")) cribEdit->setText(settings["crib"].toString());
    if (settings.contains("cipher")) cipherEdit->setText(settings["cipher"].toString());
    if (settings.contains("rotor1")) rotor1Combo->setCurrentText(settings["rotor1"].toString());
    if (settings.contains("rotor2")) rotor2Combo->setCurrentText(settings["rotor2"].toString());
    if (settings.contains("rotor3")) rotor3Combo->setCurrentText(settings["rotor3"].toString());
    if (settings.contains("reflector")) reflectorCombo->setCurrentText(settings["reflector"].toString());
    if (settings.contains("testAllOrders")) testAllOrdersCheck->setChecked(settings["testAllOrders"].toBool());
    if (settings.contains("searchWithoutPlugboard")) searchWithoutPlugboardCheck->setChecked(settings["searchWithoutPlugboard"].toBool());
    
    QMessageBox::information(this, "Success", "設定が読み込まれました");
}

void BombeWindow::onExportResultsClicked() {
    if (allResults.empty()) {
        QMessageBox::warning(this, "Error", "エクスポートする結果がありません");
        return;
    }
    
    QString fileName = QFileDialog::getSaveFileName(this, 
        "Export Results", "bombe_results.json", "JSON Files (*.json)");
    
    if (fileName.isEmpty()) return;
    
    QJsonObject root;
    
    // Settings
    QJsonObject settings;
    settings["crib"] = cribEdit->text();
    settings["cipher"] = cipherEdit->text();
    settings["rotor1"] = rotor1Combo->currentText();
    settings["rotor2"] = rotor2Combo->currentText();
    settings["rotor3"] = rotor3Combo->currentText();
    settings["reflector"] = reflectorCombo->currentText();
    settings["testAllOrders"] = testAllOrdersCheck->isChecked();
    settings["searchWithoutPlugboard"] = searchWithoutPlugboardCheck->isChecked();
    root["settings"] = settings;
    
    // Results
    QJsonArray resultsArray;
    for (const auto& result : allResults) {
        QJsonObject resultObj;
        resultObj["position"] = QString::fromStdString(result.getPositionString());
        resultObj["rotors"] = QString::fromStdString(result.getRotorString());
        resultObj["score"] = result.score;
        resultObj["matchRate"] = result.matchRate;
        resultObj["plugboardPairs"] = result.plugboardPairs;
        resultObj["offset"] = result.offset;
        
        // Plugboard
        QJsonArray plugboardArray;
        for (const auto& [a, b] : result.plugboard) {
            QString pair;
            pair += a;
            pair += b;
            plugboardArray.append(pair);
        }
        resultObj["plugboard"] = plugboardArray;
        
        resultsArray.append(resultObj);
    }
    root["results"] = resultsArray;
    root["totalResults"] = static_cast<int>(allResults.size());
    
    QJsonDocument doc(root);
    QFile file(fileName);
    if (file.open(QIODevice::WriteOnly)) {
        file.write(doc.toJson());
        file.close();
        QMessageBox::information(this, "Success", 
            QString("結果が %1 にエクスポートされました").arg(QFileInfo(fileName).fileName()));
    } else {
        QMessageBox::warning(this, "Error", "Failed to save file!");
    }
}

void BombeWindow::onResultSelected() {
    auto items = resultsList->selectedItems();
    if (items.isEmpty()) return;
    
    int index = resultsList->row(items.first());
    if (index < 0 || index >= allResults.size()) return;
    
    const auto& result = allResults[index];
    
    QString detail = QString("Selected: #%1\n"
                           "Position: %2, Rotors: %3\n"
                           "Match rate: %4%, Plugboard pairs: %5\n"
                           "Crib offset: %6")
        .arg(index + 1)
        .arg(QString::fromStdString(result.getPositionString()))
        .arg(QString::fromStdString(result.getRotorString()))
        .arg(result.matchRate * 100, 0, 'f', 1)
        .arg(result.plugboardPairs)
        .arg(result.offset);
    
    logEdit->append("\n" + detail);
}

void BombeWindow::onAttackProgress(const QString& message) {
    logEdit->append(message);
}

void BombeWindow::onAttackFinished(const std::vector<BombeResult>& results) {
    allResults = results;
    showResults(results);
    
    startButton->setEnabled(true);
    stopButton->setEnabled(false);
    progressBar->setVisible(false);
    exportButton->setEnabled(!results.empty());
}

void BombeWindow::onAttackError(const QString& error) {
    QMessageBox::critical(this, "Error", error);
    
    startButton->setEnabled(true);
    stopButton->setEnabled(false);
    progressBar->setVisible(false);
}

void BombeWindow::showResults(const std::vector<BombeResult>& results) {
    if (results.empty()) {
        resultLabel->setText("有効なローター位置が見つかりませんでした");
        return;
    }
    
    resultLabel->setText(QString("Found %1 candidates").arg(results.size()));
    
    resultsList->clear();
    for (size_t i = 0; i < std::min(size_t(50), results.size()); ++i) {
        const auto& result = results[i];
        QString plugboardStr = "None";
        if (!result.plugboard.empty()) {
            QStringList pairs;
            for (const auto& [a, b] : result.plugboard) {
                pairs << QString("%1%2").arg(a).arg(b);
            }
            plugboardStr = pairs.join(" ");
        }
        
        QString item = QString("#%1: %2 (%3) - Score: %4, Match: %5%, Plugboard: %6, Offset: %7")
            .arg(i + 1)
            .arg(QString::fromStdString(result.getPositionString()))
            .arg(QString::fromStdString(result.getRotorString()))
            .arg(result.score, 0, 'f', 1)
            .arg(result.matchRate * 100, 0, 'f', 1)
            .arg(plugboardStr)
            .arg(result.offset);
        resultsList->addItem(item);
    }
    
    if (!results.empty()) {
        resultsList->setCurrentRow(0);
    }
}

// BombeWorker implementation
BombeWorker::BombeWorker() : stopFlag(false) {}

void BombeWorker::doAttack(const QString& crib, const QString& cipher,
                           const QStringList& rotors, const QString& reflector,
                           bool testAllOrders, bool searchWithoutPlugboard) {
    emit progress("=== Starting Bombe Attack ===");
    emit progress(QString("Crib: %1").arg(crib));
    emit progress(QString("Cipher: %1").arg(cipher));
    
    if (testAllOrders) {
        emit progress(QString("Test all rotor orders: ON (testing all combinations of %1 rotors)").arg(rotors.size()));
    } else {
        emit progress(QString("Test all rotor orders: OFF (testing only %1-%2-%3)")
            .arg(rotors[0]).arg(rotors[1]).arg(rotors[2]));
    }
    
    std::string cribStr = crib.toStdString();
    std::string cipherStr = cipher.toStdString();
    std::string reflectorStr = reflector.toStdString();
    
    std::vector<std::string> rotorTypes;
    for (const auto& r : rotors) {
        rotorTypes.push_back(r.toStdString());
    }
    
    // Use BombeAttack class for historically accurate implementation
    BombeAttack bombeAttack(cribStr, cipherStr, rotorTypes, reflectorStr, testAllOrders, searchWithoutPlugboard);
    
    // Progress callback
    auto progressCallback = [this](const std::string& msg) {
        if (!stopFlag) {
            emit progress(QString::fromStdString(msg));
        }
    };
    
    // Run the attack
    progressCallback("Starting Bombe attack with proper plugboard deduction...");
    auto candidateResults = bombeAttack.attack(progressCallback);
    
    if (stopFlag) {
        bombeAttack.stop();
        emit finished(std::vector<BombeResult>{});
        return;
    }
    
    // Convert CandidateResult to BombeResult
    std::vector<BombeResult> results;
    for (const auto& candidate : candidateResults) {
        BombeResult result;
        result.score = candidate.score;
        result.positions = candidate.positions;
        result.rotorOrder = candidate.rotorOrder;
        result.plugboard = candidate.plugboard;
        result.matchRate = candidate.matchRate;
        result.plugboardPairs = candidate.plugboardPairs;
        result.offset = candidate.offset;
        results.push_back(result);
    }
    
    emit progress(QString("\nFound %1 possible settings").arg(results.size()));
    
    // Show top 10
    for (size_t i = 0; i < std::min(size_t(10), results.size()); ++i) {
        const auto& r = results[i];
        QString plugboardStr;
        for (const auto& [a, b] : r.plugboard) {
            if (!plugboardStr.isEmpty()) plugboardStr += " ";
            plugboardStr += QString("%1%2").arg(a).arg(b);
        }
        
        emit progress(QString("  #%1: %2 (Rotors: %3) - Score: %4, Match: %5%, "
                           "Plugboard: %6, Offset: %7")
            .arg(i + 1)
            .arg(QString::fromStdString(r.getPositionString()))
            .arg(QString::fromStdString(r.getRotorString()))
            .arg(r.score, 0, 'f', 1)
            .arg(r.matchRate * 100, 0, 'f', 1)
            .arg(plugboardStr.isEmpty() ? "None" : plugboardStr)
            .arg(r.offset));
    }
    
    emit progress("\n=== Bombe Attack Completed ===");
    emit finished(results);
}

// testPosition method removed - now using BombeAttack class
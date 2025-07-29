#ifndef BOMBE_WINDOW_H
#define BOMBE_WINDOW_H

#include <QMainWindow>
#include <QThread>
#include <memory>
#include <vector>
#include <atomic>
#include "../core/BombeAttack.h"

QT_BEGIN_NAMESPACE
class QLineEdit;
class QTextEdit;
class QComboBox;
class QCheckBox;
class QPushButton;
class QProgressBar;
class QListWidget;
class QLabel;
QT_END_NAMESPACE

class BombeWorker;

struct BombeResult {
    double score;
    std::vector<int> positions;
    std::vector<std::string> rotorOrder;
    std::vector<std::pair<char, char>> plugboard;
    double matchRate;
    int plugboardPairs;
    int offset;
    
    std::string getPositionString() const {
        std::string result;
        for (int pos : positions) {
            result += char('A' + pos);
        }
        return result;
    }
    
    std::string getRotorString() const {
        std::string result;
        for (size_t i = 0; i < rotorOrder.size(); ++i) {
            if (i > 0) result += "-";
            result += rotorOrder[i];
        }
        return result;
    }
};

class BombeWindow : public QMainWindow {
    Q_OBJECT

public:
    BombeWindow(QWidget *parent = nullptr);
    ~BombeWindow();

signals:
    void startAttack(const QString& crib, const QString& cipher,
                    const QStringList& rotors, const QString& reflector,
                    bool testAllOrders, bool searchWithoutPlugboard);

private slots:
    void onStartAttackClicked();
    void onStopAttackClicked();
    void onClearLogClicked();
    void onSaveSettingsClicked();
    void onLoadSettingsClicked();
    void onExportResultsClicked();
    void onResultSelected();
    
    void onAttackProgress(const QString& message);
    void onAttackFinished(const std::vector<BombeResult>& results);
    void onAttackError(const QString& error);

private:
    void setupUi();
    void showResults(const std::vector<BombeResult>& results);
    
    // UI elements
    QLineEdit* cribEdit;
    QLineEdit* cipherEdit;
    QComboBox* rotor1Combo;
    QComboBox* rotor2Combo;
    QComboBox* rotor3Combo;
    QComboBox* reflectorCombo;
    QCheckBox* testAllOrdersCheck;
    QCheckBox* searchWithoutPlugboardCheck;
    
    QTextEdit* logEdit;
    QListWidget* resultsList;
    QLabel* resultLabel;
    
    QPushButton* startButton;
    QPushButton* stopButton;
    QPushButton* clearButton;
    QPushButton* saveSettingsButton;
    QPushButton* loadSettingsButton;
    QPushButton* exportButton;
    
    QProgressBar* progressBar;
    
    // Worker thread
    QThread* workerThread;
    BombeWorker* worker;
    
    // Results
    std::vector<BombeResult> allResults;
};

// Worker class for background processing
class BombeWorker : public QObject {
    Q_OBJECT

public:
    BombeWorker();
    
    void stop() { stopFlag = true; }

public slots:
    void doAttack(const QString& crib, const QString& cipher,
                  const QStringList& rotors, const QString& reflector,
                  bool testAllOrders, bool searchWithoutPlugboard);

signals:
    void progress(const QString& message);
    void finished(const std::vector<BombeResult>& results);
    void error(const QString& error);

private:
    std::atomic<bool> stopFlag{false};
};

#endif // BOMBE_WINDOW_H
#ifndef ENIGMA_MAIN_WINDOW_H
#define ENIGMA_MAIN_WINDOW_H

#include <QMainWindow>
#include <memory>
#include <vector>
#include <string>

QT_BEGIN_NAMESPACE
class QComboBox;
class QLineEdit;
class QTextEdit;
class QPushButton;
class QLabel;
QT_END_NAMESPACE

class EnigmaMachine;

class EnigmaMainWindow : public QMainWindow {
    Q_OBJECT

public:
    EnigmaMainWindow(QWidget *parent = nullptr);
    ~EnigmaMainWindow();

private slots:
    void onEncryptClicked();
    void onSaveConfigClicked();
    void onLoadConfigClicked();
    void onImportBombeResultClicked();
    void onOpenBombeClicked();
    void updateRotorPositions();

private:
    void setupUi();
    void setupEnigmaMachine();
    void updateEnigmaFromUi();
    std::string getPlugboardString() const;
    void setPlugboardFromString(const std::string& str);

    // UI elements
    QComboBox* rotor1TypeCombo;
    QComboBox* rotor2TypeCombo;
    QComboBox* rotor3TypeCombo;
    QComboBox* reflectorCombo;
    
    QLineEdit* rotor1PosEdit;
    QLineEdit* rotor2PosEdit;
    QLineEdit* rotor3PosEdit;
    
    QLineEdit* rotor1RingEdit;
    QLineEdit* rotor2RingEdit;
    QLineEdit* rotor3RingEdit;
    
    QLineEdit* plugboardEdit;
    QTextEdit* inputTextEdit;
    QTextEdit* outputTextEdit;
    
    QPushButton* encryptButton;
    QPushButton* saveConfigButton;
    QPushButton* loadConfigButton;
    QPushButton* importBombeButton;
    QPushButton* openBombeButton;
    
    // Enigma machine
    std::unique_ptr<EnigmaMachine> enigmaMachine;
};

#endif // ENIGMA_MAIN_WINDOW_H
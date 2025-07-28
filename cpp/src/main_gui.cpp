#include <QApplication>
#include "gui/EnigmaMainWindow.h"

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    
    app.setApplicationName("Enigma Simulator");
    app.setOrganizationName("EnigmaProject");
    
    EnigmaMainWindow window;
    window.show();
    
    return app.exec();
}
@echo off
echo Starting Bombe Simulator...

rem Check if JAR with dependencies exists
if not exist target\enigma-simulator-1.0.0-jar-with-dependencies.jar (
    echo ERROR: JAR file not found. Please build the project first using: mvn clean package
    pause
    exit /b 1
)

rem Run the JAR with JavaFX runtime
java -Djava.library.path="javafx-jars" --module-path "javafx-jars" --add-modules javafx.controls,javafx.fxml -cp target\enigma-simulator-1.0.0-jar-with-dependencies.jar com.enigma.gui.BombeGUI

pause
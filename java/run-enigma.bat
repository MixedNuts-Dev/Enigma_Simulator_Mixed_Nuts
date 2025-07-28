@echo off
echo Starting Enigma Simulator...

rem Check if JAR with dependencies exists
if not exist target\enigma-simulator-1.0.0-jar-with-dependencies.jar (
    echo ERROR: JAR file not found. Please build the project first using: mvn clean package
    pause
    exit /b 1
)

rem Run the JAR with dependencies (includes JavaFX)
java -jar target\enigma-simulator-1.0.0-jar-with-dependencies.jar

pause
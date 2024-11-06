#!/bin/bash

# Name der virtuellen Umgebung
VENV_DIR="venv"

# Python-Version prüfen
PYTHON_VERSION=$(python3 --version 2>&1)

if [[ $PYTHON_VERSION != "Python 3."* ]]; then
    echo "Python 3 wird benötigt. Bitte installieren Sie Python 3."
    exit 1
fi

# Virtuelle Umgebung erstellen, falls sie nicht existiert
if [ ! -d "$VENV_DIR" ]; then
    echo "Erstelle virtuelle Umgebung in '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
fi

# Virtuelle Umgebung aktivieren
source $VENV_DIR/bin/activate

# Paketliste für Abhängigkeiten, falls vorhanden
REQUIREMENTS=(
    "PyPDF2"
    "pytesseract"              # Ersatz für "ocr"
    "opencv-python-headless"    # OpenCV
    "numpy"
    "pdf2image"
    "pillow"                    # Pillow statt PIL
)

echo "Installiere benötigte Pakete..."
for package in "${REQUIREMENTS[@]}"; do
    pip install "$package" || echo "Warnung: $package konnte nicht installiert werden."
done

echo "Pakete wurden, falls möglich, installiert."

# Deaktivieren der virtuellen Umgebung
deactivate

echo "Setup abgeschlossen! Die virtuelle Umgebung befindet sich in '$VENV_DIR'."

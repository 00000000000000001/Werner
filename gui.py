import tkinter as tk
from tkinter import filedialog
import os
import PyPDF2
import convert
import sys
import subprocess
import trace

class PDFDCTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Werner der PDF Konverter")
        self.root.geometry("400x150")

        # Desktop-Pfad für die Plattform ermitteln
        self.desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        # Schaltfläche zum Auswählen von PDF-Dateien
        self.select_button = tk.Button(root, text="PDFs auswählen", command=self.select_pdfs, bg="lightblue", width=20, height=2)
        self.select_button.pack(pady=20)

        # Ergebnis-Label für Abschluss- oder Fehlermeldungen
        self.result_label = tk.Label(root, text="", fg="green")
        self.result_label.pack(pady=10)

    def select_pdfs(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF Dateien", "*.pdf")])
        if not file_paths:
            self.result_label.config(text="Keine PDF-Dateien ausgewählt.", fg="red")
            return

        print("Gefundene PDF-Dateien:", file_paths)
        self.process_pdf(file_paths)

    def join_pdfs(self, pdf_paths, output_path="merged_output.pdf"):
        pdf_writer = PyPDF2.PdfWriter()
        for pdf_path in pdf_paths:
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_path)
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                print(f"{pdf_path} erfolgreich hinzugefügt.")
            except Exception as e:
                print(f"Fehler beim Hinzufügen von {pdf_path}: {e}")

        with open(output_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)
        print(f"Zusammengefügte PDF gespeichert unter: {output_path}")
        return output_path

    def speichern(self, data):
        # Speichern auf dem Desktop
        output_path = os.path.join(self.desktop_dir, "Formular.dict")
        with open(output_path, "w", encoding="latin-1") as file:
            file.write(data)
        return output_path

    def process_pdf(self, pdfs):
        merged_pdf_path = self.join_pdfs(pdfs)
        try:
            processed_data = convert.convert(merged_pdf_path)
            output_path = self.speichern(processed_data)
            os.remove(merged_pdf_path)
            print(f"{merged_pdf_path} erfolgreich gelöscht.")
            self.result_label.config(text=f"Datei gespeichert unter: {output_path}", fg="green")

            # Öffnen des Desktop-Ordners
            self.open_folder(self.desktop_dir)

        except Exception as e:
            print(f"Fehler beim Verarbeiten der PDF-Dateien: {e}")
            self.result_label.config(text=f"Fehler: {e}", fg="red")
            import traceback
            traceback.print_exc()

    def open_folder(self, path):
        """Öffnet den Ordner im System-Dateiexplorer"""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            elif sys.platform == "linux":
                subprocess.Popen(["xdg-open", path])
            else:
                print("Nicht unterstütztes Betriebssystem")
        except Exception as e:
            print(f"Fehler beim Öffnen des Ordners: {e}")

# Hauptfenster initialisieren
root = tk.Tk()
app = PDFDCTApp(root)
root.mainloop()

# python3.11 -m nuitka --standalone --onefile --follow-imports --enable-plugin=tk-inter gui.py --output-dir=build

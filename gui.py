import tkinter as tk
from tkinter import filedialog
import os
import convert
import sys
import subprocess
import trace
from split_pdf import split_pdf_into_png_files

class PDFDCTApp:
    def __init__(self, root: tk.Tk):

        def split_pdfs_into_png_files(pdf_files: tuple) -> list:
            pages = []
            total_pages = 0
            for file in pdf_files:
                new_pages = split_pdf_into_png_files(file, count_offset=total_pages)
                total_pages += len(new_pages)
                pages.extend(new_pages)

            return pages

        def process_input():
            try:
                pdf_files = self.select_pdfs()

                if not pdf_files:
                    return

                png_files = split_pdfs_into_png_files(pdf_files)
                dict_string = convert.convert_pngs_to_dict_string(png_files)
                dict_output_path = self.save_as_dict(dict_string)
                self.result_label.config(text=f"Datei gespeichert unter: {dict_output_path}", fg="green")
                self.open_folder(self.desktop_dir)
            except Exception as e:
                print(f"Fehler beim Verarbeiten der PDF-Dateien: {e}")
                self.result_label.config(text=f"Fehler: {e}", fg="red")
                import traceback
                traceback.print_exc()

        self.root = root
        self.root.title("Werner der PDF Konverter")
        self.root.geometry("400x150")

        # Desktop-Pfad für die Plattform ermitteln
        self.desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

        # Schaltfläche zum Auswählen von PDF-Dateien
        self.select_button = tk.Button(root, text="PDFs auswählen", command=process_input, bg="lightblue", width=20, height=2)
        self.select_button.pack(pady=20)

        # Ergebnis-Label für Abschluss- oder Fehlermeldungen
        self.result_label = tk.Label(root, text="", fg="green")
        self.result_label.pack(pady=10)

    def select_pdfs(self) -> tuple:
        file_paths = filedialog.askopenfilenames(filetypes=[("PDF Dateien", "*.pdf")])
        if not file_paths:
            self.result_label.config(text="Keine PDF-Dateien ausgewählt.", fg="red")
            return ()
        return file_paths

    def save_as_dict(self, dict_content: str) -> str:
        output_path = os.path.join(self.desktop_dir, "Formular.dict")
        with open(output_path, "w", encoding="latin-1") as file:
            file.write(dict_content)
        return output_path

    def open_folder(self, path: str):
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

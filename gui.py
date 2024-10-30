import tkinter as tk
from tkinterdnd2 import TkinterDnD, DND_FILES
import pickle
import os
import PyPDF2
import re
import convert

class PDFDCTApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDFs zu Formular Konverter")
        self.root.geometry("300x300")

        # Drag & Drop Bereich
        self.drop_area = tk.Label(root, text="PDFs hier ablegen", bg="lightgrey", width=30, height=10)
        self.drop_area.pack(pady=20)

        # Ergebnis-Label für Abschluss- oder Fehlermeldungen
        self.result_label = tk.Label(root, text="", fg="green")
        self.result_label.pack(pady=10)

        # Drag & Drop-Ereignisbindung
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.process_pdf)

    def join_pdfs(self, pdf_paths, output_path="merged_output.pdf"):
        # Erstelle ein neues PDF-Dokument zum Zusammenfügen
        pdf_writer = PyPDF2.PdfWriter()

        # Füge jede PDF-Datei aus der Liste hinzu
        for pdf_path in pdf_paths:
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_path)
                # Füge alle Seiten der aktuellen PDF zum Writer hinzu
                for page in pdf_reader.pages:
                    pdf_writer.add_page(page)
                print(f"{pdf_path} erfolgreich hinzugefügt.")
            except Exception as e:
                print(f"Fehler beim Hinzufügen von {pdf_path}: {e}")

        # Speichere die zusammengefügte PDF-Datei
        with open(output_path, "wb") as output_pdf:
            pdf_writer.write(output_pdf)

        print(f"Zusammengefügte PDF gespeichert unter: {output_path}")
        return output_path

    def speichern(self, data):
        # Speichere Daten als Formular.dict-Datei
        output_path = "Formular.dict"
        with open(output_path, "w") as file:
            file.write(data)
        return output_path

    def process_pdf(self, event):
        # Verwende splitlist, um event.data in eine Liste von Dateipfaden zu konvertieren
        files = self.root.tk.splitlist(event.data)

        # Liste für die PDF-Dateipfade
        pdfs = []

        # Überprüfen, ob die Dateien PDF-Dateien sind und sie der Liste hinzufügen
        for file_path in files:
            if file_path.lower().endswith('.pdf'):
                pdfs.append(file_path)
            else:
                print(f"Warnung: {file_path} ist keine PDF-Datei und wird übersprungen.")

        # Ausgabe der Liste der PDF-Dateipfade
        print("Gefundene PDF-Dateien:", pdfs)

        if not pdfs:
            self.result_label.config(text="Keine gültigen PDF-Dateien gefunden.", fg="red")
            return

        # Mergen der PDF-Dateien
        merged_pdf_path = self.join_pdfs(pdfs)

        try:
            # Verarbeiten der gemergten PDF-Datei
            processed_data = convert.convert(merged_pdf_path)  # Annahme: convert gibt ein Dictionary zurück

            # Speichern der verarbeiteten Daten als Formular.dict Datei
            output_path = self.speichern(processed_data)

            # Lösche die gemergte PDF-Datei von der Festplatte
            os.remove(merged_pdf_path)
            print(f"{merged_pdf_path} erfolgreich gelöscht.")

            # Zeige Speicherort an
            self.result_label.config(text=f"Datei gespeichert unter: {output_path}", fg="green")
        except Exception as e:
            print(f"Fehler beim Verarbeiten der PDF-Dateien: {e}")
            self.result_label.config(text=f"Fehler: {e}", fg="red")

# Hauptfenster initialisieren
root = TkinterDnD.Tk()
app = PDFDCTApp(root)
root.mainloop()

from typing import List
import random
import base64
import hashlib
from PIL import Image
from Klassen import Textfeld, Ankreuzfeld
import os
from io import BytesIO
from utils import *

class Formular:

    def __init__(self, name: str, dpi: int):
        self.name = name
        self.dpi = dpi
        self.pages = []
        self.element_counter = 0

    def generate_ident(self):
        return str(random.randint(10**17, 10**18 - 1))

    def img_to_base64(self, pil_image: Image.Image) -> str:
        buffer = BytesIO()

        pil_image.save(buffer, format="PNG")

        base64_encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return base64_encoded

    def calculate_md5(self, pil_image: Image.Image) -> str:
        """
        Berechnet den MD5-Hash eines PIL-Bildes.

        Args:
            pil_image (Image.Image): Das PIL-Bild, dessen MD5-Hash berechnet werden soll.

        Returns:
            str: Der MD5-Hash des Bildes als hexadezimale Zeichenkette.
        """
        hash_md5 = hashlib.md5()

        # Bild in einen Speicherpuffer schreiben
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")  # Du kannst das Format anpassen (z.B. "JPEG")
        buffer.seek(0)  # Zurück zum Anfang des Puffers

        # Pufferinhalt blockweise lesen und MD5-Hash berechnen
        for chunk in iter(lambda: buffer.read(4096), b""):
            hash_md5.update(chunk)

        # MD5-Hash als hexadezimale Zeichenkette zurückgeben
        return hash_md5.hexdigest()

    def elements_to_xml(self, elemente: List) -> List[str]:
        elements_xml = []

        for i, e in enumerate(elemente):
            e_xml = ""

            if isinstance(e, Textfeld):
                e_xml = f"""<dict>
                   	<key>feldName</key>
                   	<string>v{self.element_counter + 1}</string>
                   	<key>font</key>
                   	<string>Courier</string>
                   	<key>fontSize</key>
                   	<integer>18</integer>
                   	<key>height</key>
                   	<real>{round(pixel_to_mm(e.rechts_unten.y-e.links_oben.y, self.dpi), 2)}</real>
                   	<key>ident</key>
                   	<integer>{self.generate_ident()}</integer>
                   	<key>isMandatory</key>
                   	<integer>0</integer>
                   	<key>listenpos</key>
                   	<integer>{i + 1}</integer>
                   	<key>modus</key>
                   	<integer>2</integer>
                   	<key>noPrefillAtCopyFromVorlage</key>
                   	<integer>1</integer>
                   	<key>showInKarteitext</key>
                   	<integer>0</integer>
                   	<key>visible</key>
                   	<integer>1</integer>
                   	<key>width</key>
                   	<real>{round(pixel_to_mm(e.rechts_unten.x-e.links_oben.x, self.dpi), 2)}</real>
                   	<key>xpos</key>
                   	<real>{round(pixel_to_mm(e.links_oben.x, self.dpi), 2)}</real>
                   	<key>ypos</key>
                   	<real>{round(pixel_to_mm(e.links_oben.y, self.dpi), 2)}</real>
                </dict>"""
                self.element_counter += 1
                elements_xml.append(e_xml)

            if isinstance(e, Ankreuzfeld):
                e_xml = f"""<dict>
                   	<key>feldName</key>
                   	<string>v{self.element_counter + 1}</string>
                   	<key>font</key>
                   	<string>Courier</string>
                   	<key>fontSize</key>
                   	<integer>18</integer>
                   	<key>height</key>
                   	<real>{round(pixel_to_mm(e.rechts_unten.y-e.links_oben.y, self.dpi), 2)}</real>
                   	<key>ident</key>
                   	<integer>{self.generate_ident()}</integer>
                   	<key>listenpos</key>
                   	<integer>{i + 1}</integer>
                   	<key>modus</key>
                   	<integer>4</integer>
                   	<key>showInKarteitext</key>
                   	<integer>0</integer>
                   	<key>visible</key>
                   	<integer>1</integer>
                   	<key>width</key>
                   	<real>{round(pixel_to_mm(e.rechts_unten.x-e.links_oben.x, self.dpi), 2)}</real>
                   	<key>xpos</key>
                   	<real>{round(pixel_to_mm(e.links_oben.x, self.dpi), 2)}</real>
                   	<key>ypos</key>
                   	<real>{round(pixel_to_mm(e.links_oben.y, self.dpi), 2)}</real>
                </dict>"""
                self.element_counter += 1
                elements_xml.append(e_xml)

        return elements_xml

    def new_page(self, elemente: List, pil_image: Image.Image):


        self.height = pil_image.height
        self.width = pil_image.width

        page_xml = f"""
        <dict>
    		<key>currentImage</key>
    		<dict>
    			<key>datum</key>
    			<date>2024-10-28T14:48:37Z</date>
    			<key>ident</key>
    			<integer>{self.generate_ident()}</integer>
    			<key>image</key>
    			<string>{self.img_to_base64(pil_image)}</string>
    			<key>md5</key>
    			<string>{self.calculate_md5(pil_image)}</string>
    		</dict>
    		<key>customFormularElemente</key>
    		<dict>
    			<key>archivedObjects</key>
    			<array/>
    			<key>cleanedArray</key>
    			<array>
    			    {''.join(self.elements_to_xml(elemente))}
    			</array>
    			<key>isArchivedArray</key>
    			<true/>
    		</dict>
    		<key>ident</key>
    		<integer>{self.generate_ident()}</integer>
    		<key>page</key>
    		<integer>{len(self.pages) + 1}</integer>
    	</dict>"""

        self.pages.append(page_xml)

    # def speichere_mit_nummerierung(self, speicherpfad: str, outer_xml: str):
    #     os.makedirs(speicherpfad, exist_ok=True)

    #     # Basisdateiname
    #     base_filename = "Formular"
    #     extension = ".dict"
    #     file_path = os.path.join(speicherpfad, base_filename + extension)

    #     # Prüfe, ob die Datei existiert, und finde die nächste verfügbare Nummer
    #     counter = 1
    #     while os.path.exists(file_path):
    #         file_path = os.path.join(speicherpfad, f"{base_filename}_{counter}{extension}")
    #         counter += 1

    #     # Speichern der Datei
    #     with open(file_path, "w", encoding="utf-8") as file:
    #         file.write(outer_xml)

    #     print(f"Datei gespeichert unter: {file_path}")


    def write(self, speicherpfad: str):

        outer_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
    	<key>art</key>
    	<integer>4</integer>
    	<key>customFormular</key>
    	<integer>1</integer>
    	<key>customFormularDefaultTyp</key>
    	<integer>0</integer>
    	<key>customFormularPages</key>
    	<dict>
    		<key>archivedObjects</key>
    		<array/>
    		<key>cleanedArray</key>
    		<array>
    		  {''.join(self.pages)}
    		</array>
    		<key>isArchivedArray</key>
    		<true/>
    	</dict>
    	<key>font</key>
    	<string>Courier</string>
    	<key>fontsize</key>
    	<real>18</real>
    	<key>formEditableLists</key>
    	<dict>
    		<key>archivedObjects</key>
    		<array/>
    		<key>cleanedArray</key>
    		<array/>
    		<key>isArchivedArray</key>
    		<true/>
    	</dict>
    	<key>ident</key>
    	<integer>{self.generate_ident()}</integer>
    	<key>kategorie</key>
    	<string>Custom-Formulare</string>
    	<key>kuerzel</key>
    	<string>{self.name}</string>
    	<key>listenposition</key>
    	<integer>1</integer>
    	<key>name</key>
    	<string>CustomFormular_173892287</string>
    	<key>numberOfDirectPages</key>
    	<integer>{len(self.pages)}</integer>
    	<key>papersize_height</key>
    	<real>{int(pixel_to_points(self.height, self.dpi))}</real>
    	<key>papersize_width</key>
    	<real>{int(pixel_to_points(self.width, self.dpi))}</real>
    	<key>tooltip</key>
    	<string>{self.name}</string>
    	<key>version</key>
    	<string>v1.64</string>
    	<key>visible</key>
    	<integer>1</integer>
    	<key>xibfile</key>
    	<string>CustomFormular</string>
        </dict>
        </plist>"""

        with open(speicherpfad, "w", encoding="utf-8") as file:
            file.write(outer_xml)

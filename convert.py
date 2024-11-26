import random
import shutil
import os
from PIL import Image
import base64
from io import BytesIO
import ocr
from klassen import Ankreuzfeld, Textfeld, Rechteck
import hashlib

global_counter = 0

def calculate_md5(file_path: str) -> str:
    """
    Berechnet den MD5-Hash einer Datei (z.B. JPEG-Datei).

    Args:
        file_path (str): Der Pfad zur Datei, deren MD5-Hash berechnet werden soll.

    Returns:
        str: Der MD5-Hash der Datei als hexadezimale Zeichenkette.
    """
    hash_md5 = hashlib.md5()

    # Öffnet die Datei im Binärmodus und liest sie in Blöcken
    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(4096), b""):
            hash_md5.update(chunk)

    # Gibt den MD5-Hash als hexadezimale Zeichenkette zurück
    return hash_md5.hexdigest()

def convert_png_to_jpeg(png_path: str, quality: int = 90) -> str:
    """
    Konvertiert ein PNG-Bild im DIN-A4-Format in ein JPEG-Bild mit komprimierter Qualität, um die Dateigröße zu reduzieren.

    Args:
        png_path (str): Der Pfad zur PNG-Datei.
        quality (int): Die Qualität des JPEG-Bildes (zwischen 1 und 95, höhere Werte bedeuten bessere Qualität und größere Dateigröße).
        output_path (str): Optionaler Pfad, um das konvertierte Bild zu speichern. Wenn nicht angegeben, wird derselbe Name wie der PNG-Pfad verwendet, jedoch mit der Erweiterung .jpg.

    Returns:
        str: Der Pfad zur konvertierten JPEG-Datei.
    """
    # Öffne das PNG-Bild
    with Image.open(png_path) as img:
        # Standard-Ausgabepfad verwenden, falls keiner angegeben ist
        output_path = png_path.rsplit(".", 1)[0] + ".jpg"

        # Konvertiere das Bild in RGB (JPEG unterstützt keinen Alpha-Kanal)
        img = img.convert("RGB")

        # Speichere das Bild als JPEG mit angegebener Qualität
        img.save(output_path, "JPEG", quality=quality, optimize=True)

        print(f"Bild erfolgreich konvertiert und gespeichert als: {output_path}")
        return output_path

def file_to_base64(file_path: str) -> str:
    """
    Konvertiert eine beliebige Datei in eine Base64-codierte Zeichenkette.

    Args:
        file_path (str): Der Pfad zur Datei, die in Base64 umgewandelt werden soll.

    Returns:
        str: Die Base64-codierte Zeichenkette der Datei.
    """
    with open(file_path, "rb") as file:
        file_content = file.read()
        base64_encoded = base64.b64encode(file_content).decode("utf-8")

    return base64_encoded

def generate_ident():
    return str(random.randint(10**17, 10**18 - 1))

def delete_folder(folder_name: str):
    # Überprüfen, ob der Ordner existiert
    if os.path.exists(folder_name) and os.path.isdir(folder_name):
        try:
            shutil.rmtree(folder_name)
            print(f"Ordner '{folder_name}' wurde erfolgreich gelöscht.")
        except Exception as e:
            print(f"Fehler beim Löschen des Ordners '{folder_name}': {e}")
    else:
        print(f"Ordner '{folder_name}' existiert nicht.")

def ankreuzfeld_to_xml(el: Rechteck, n: int) -> str:
    global global_counter
    global_counter += 1

    name = f"v{global_counter}"
    width = el.x2 - el.x1 if el.x2 - el.x1 >= 4 else 4
    height = el.y2 - el.y1 if el.y2 - el.y1 >= 6 else 6
    x = el.x1 - (width - (el.x2 - el.x1)) / 2
    y = el.y1 - (height - (el.y2 - el.y1)) / 2

    return f"""
    <dict>
       	<key>feldName</key>
       	<string>{name}</string>
       	<key>font</key>
       	<string>Courier</string>
       	<key>fontSize</key>
       	<integer>18</integer>
       	<key>height</key>
       	<real>{height}</real>
       	<key>ident</key>
       	<integer>{generate_ident()}</integer>
       	<key>listenpos</key>
       	<integer>{n + 1}</integer>
       	<key>modus</key>
       	<integer>4</integer>
       	<key>showInKarteitext</key>
       	<integer>0</integer>
       	<key>visible</key>
       	<integer>1</integer>
       	<key>width</key>
       	<real>{width}</real>
       	<key>xpos</key>
       	<real>{x}</real>
       	<key>ypos</key>
       	<real>{y}</real>
    </dict>"""

def textfeld_to_xml(el: Rechteck, n: int) -> str:
    global global_counter
    global_counter += 1

    name = f"v{global_counter}"
    x = el.x1
    y = el.y1
    width = el.x2 - el.x1
    hoehe = el.y2 - el.y1
    return f"""
    <dict>
       	<key>feldName</key>
       	<string>{name}</string>
       	<key>font</key>
       	<string>Courier</string>
       	<key>fontSize</key>
       	<integer>18</integer>
       	<key>height</key>
       	<real>{hoehe}</real>
       	<key>ident</key>
       	<integer>{generate_ident()}</integer>
       	<key>isMandatory</key>
       	<integer>0</integer>
       	<key>listenpos</key>
       	<integer>{n + 1}</integer>
       	<key>modus</key>
       	<integer>2</integer>
       	<key>noPrefillAtCopyFromVorlage</key>
       	<integer>1</integer>
       	<key>showInKarteitext</key>
       	<integer>0</integer>
       	<key>visible</key>
       	<integer>1</integer>
       	<key>width</key>
       	<real>{width}</real>
       	<key>xpos</key>
       	<real>{x}</real>
       	<key>ypos</key>
       	<real>{y}</real>
    </dict>"""

def berechne_bildmasse_in_mm(png_datei_pfad: str, standard_dpi: int = 300) -> tuple:
    """
    Berechnet die physischen Abmessungen eines PNG-Bildes in Millimetern.

    :param png_datei_pfad: Pfad zur PNG-Datei.
    :param standard_dpi: Standard-DPI-Wert, falls die Datei keine DPI-Informationen enthält.
    :return: Ein Tuple (breite_mm, höhe_mm).
    :raises: FileNotFoundError, ValueError
    """
    if not os.path.exists(png_datei_pfad):
        raise FileNotFoundError(f"Die Datei '{png_datei_pfad}' wurde nicht gefunden.")

    try:
        with Image.open(png_datei_pfad) as img:
            # Versuche, die DPI-Informationen aus den Metadaten zu extrahieren
            info = img.info
            dpi = None

            if 'dpi' in info:
                dpi = info['dpi']
                if isinstance(dpi, tuple):
                    # Durchschnittliche DPI berechnen, falls unterschiedliche Werte für x und y
                    dpi_x, dpi_y = dpi
                else:
                    dpi_x = dpi_y = dpi
            else:
                # DPI-Informationen nicht gefunden, Standardwert verwenden
                dpi_x = dpi_y = standard_dpi
                print(f"DPI-Informationen nicht gefunden. Verwende Standard-DPI: {standard_dpi}")

            # Berechnung der mm pro Pixel
            mm_pro_pixel_x = 25.4 / dpi_x
            mm_pro_pixel_y = 25.4 / dpi_y

            # Bildabmessungen in Pixel
            breite_px, höhe_px = img.size

            # Berechnung der physischen Abmessungen in mm
            breite_mm = breite_px * mm_pro_pixel_x
            hoehe_mm = höhe_px * mm_pro_pixel_y

            return (breite_mm, hoehe_mm)

    except Exception as e:
        raise ValueError(f"Fehler beim Verarbeiten der Datei '{png_datei_pfad}': {e}")

def mm_in_punkte(breite_mm: int, hoehe_mm: int) -> tuple:
    """
    Konvertiert Breite und Höhe von Millimetern in ganze Punkte.

    :param breite_mm: Breite in Millimetern.
    :param hoehe_mm: Höhe in Millimetern.
    :return: Tuple mit Breite und Höhe in Punkten (breite_pt, hoehe_pt), gerundet auf ganze Zahlen.
    """
    # Umrechnungsfaktor von mm zu Punkten
    mm_zu_punkt = 72 / 25.4  # ≈ 2.83465

    # Umrechnung und Rundung auf ganze Zahlen
    breite_pt = int(breite_mm * mm_zu_punkt)
    hoehe_pt = int(hoehe_mm * mm_zu_punkt)

    return (breite_pt, hoehe_pt)

def convert_pngs_to_dict_string(png_files: list):
    global global_counter
    global_counter = 0

    name = "OCR"

    pages_xml: list = []

    bildmasse_in_punkte: tuple = (595, 840)

    for m, file in enumerate(png_files):

        bildmasse_in_mm = berechne_bildmasse_in_mm(file)
        bildmasse_in_punkte = mm_in_punkte(bildmasse_in_mm[0], bildmasse_in_mm[1])

        arr_felder = []

        # ocr.erkenne_text_und_rahmen(file)
        # quit()

        arr_felder.extend(ocr.erkenne_kleine_kreise(file, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1]))
        arr_felder.extend(ocr.erkenne_kleine_rechtecke(file, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1]))
        arr_felder.extend(ocr.erkenne_linien(file, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1]))
        arr_felder.extend(ocr.erkenne_linien_gepunktet(file, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1]))
        arr_felder.extend(ocr.erkenne_zellen(file))

        tolerance = 2  # Toleranz in mm
        arr_felder.sort(
            key=lambda pos: (
                int((pos.y1 + tolerance / 2) / tolerance),
                pos.x1
            )
        )

        arr_felder_xml: list = []

        for n, el in enumerate(arr_felder):
            if (isinstance(el, Ankreuzfeld)):
                arr_felder_xml.append(ankreuzfeld_to_xml(el, n))
            if (isinstance(el, Textfeld)):
                arr_felder_xml.append(textfeld_to_xml(el, n))


        small_file = convert_png_to_jpeg(file)

        page_xml = f"""
        <dict>
    		<key>currentImage</key>
    		<dict>
    			<key>datum</key>
    			<date>2024-10-28T14:48:37Z</date>
    			<key>ident</key>
    			<integer>{generate_ident()}</integer>
    			<key>image</key>
    			<string>{file_to_base64(small_file)}</string>
    			<key>md5</key>
    			<string>{calculate_md5(small_file)}</string>
    		</dict>
    		<key>customFormularElemente</key>
    		<dict>
    			<key>archivedObjects</key>
    			<array/>
    			<key>cleanedArray</key>
    			<array>
    			    {''.join(arr_felder_xml)}
    			</array>
    			<key>isArchivedArray</key>
    			<true/>
    		</dict>
    		<key>ident</key>
    		<integer>{generate_ident()}</integer>
    		<key>page</key>
    		<integer>{m + 1}</integer>
    	</dict>"""

        pages_xml.append(page_xml)


    frame_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
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
		  {''.join(pages_xml)}
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
	<integer>{generate_ident()}</integer>
	<key>kategorie</key>
	<string>Custom-Formulare</string>
	<key>kuerzel</key>
	<string>{name}</string>
	<key>listenposition</key>
	<integer>1</integer>
	<key>name</key>
	<string>CustomFormular_173892287</string>
	<key>numberOfDirectPages</key>
	<integer>{len(pages_xml)}</integer>
	<key>papersize_height</key>
	<real>{bildmasse_in_punkte[1]}</real>
	<key>papersize_width</key>
	<real>{bildmasse_in_punkte[0]}</real>
	<key>tooltip</key>
	<string>{name}</string>
	<key>version</key>
	<string>v1.64</string>
	<key>visible</key>
	<integer>1</integer>
	<key>xibfile</key>
	<string>CustomFormular</string>
    </dict>
    </plist>
    """


    print(f"'formular.dict' erstellt. Elemente: {global_counter}.")

    delete_folder("output_images")

    return frame_xml

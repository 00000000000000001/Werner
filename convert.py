import random
import ocr
import split_pdf
import shutil
import os
import pdf_to_b64
from PIL import Image
from klassen import Ankreuzfeld, Textfled, Feld

global_counter = 0

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

def ankreuzfeld_to_xml(el: Feld, n: int) -> str:
    global global_counter
    global_counter += 1

    name = f"v{global_counter}"
    width = 4.8038711547851562
    height = 6

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
       	<real>{el.x_in_mm - width / 2}</real>
       	<key>ypos</key>
       	<real>{el.y_in_mm - height / 2}</real>
    </dict>"""

def textfeld_to_xml(el: Feld, n: int) -> str:
    global global_counter
    global_counter += 1

    name = f"v{global_counter}"
    x = el.x_in_mm
    y = el.y_in_mm - 5 # bisschen höher, ne?
    width = el.w_in_mm
    return f"""
    <dict>
       	<key>feldName</key>
       	<string>{name}</string>
       	<key>font</key>
       	<string>Courier</string>
       	<key>fontSize</key>
       	<integer>18</integer>
       	<key>height</key>
       	<real>6</real>
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

def convert(pdf_file_path: str):
    global global_counter
    global_counter = 0

    name = "OCR"

    pages = split_pdf.pdf_to_png(pdf_file_path)

    pages_b64 = pdf_to_b64.pdf_to_base64_pages(pdf_file_path)

    seite_liste: list = []

    bildmasse_in_punkte: tuple = (595, 840)

    for m, page in enumerate(pages):

        bildmasse_in_mm = berechne_bildmasse_in_mm(page)
        bildmasse_in_punkte = mm_in_punkte(bildmasse_in_mm[0], bildmasse_in_mm[1])

        arr_ankreuzfelder_rund_koord = ocr.runde_ankreuzfelder(page, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1])
        arr_ankreuzfelder_quadratisch_koord = ocr.quadratische_ankreuzfelder(page, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1])
        arr_textfelder_koord = ocr.textfelder(page, bildbreite_mm=bildmasse_in_mm[0], bildhoehe_mm=bildmasse_in_mm[1])

        arr_felder = []
        arr_felder.extend(arr_ankreuzfelder_rund_koord)
        arr_felder.extend(arr_ankreuzfelder_quadratisch_koord)
        arr_felder.extend(arr_textfelder_koord)

        tolerance = 2  # Toleranz in mm
        arr_felder.sort(
            key=lambda pos: (
                int((pos.y_in_mm + tolerance / 2) / tolerance),
                pos.x_in_mm
            )
        )


        arr_felder_xml: list = []

        for n, el in enumerate(arr_felder):
            if (isinstance(el, Ankreuzfeld)):
                arr_felder_xml.append(ankreuzfeld_to_xml(el, n))
            if (isinstance(el, Textfled)):
                arr_felder_xml.append(textfeld_to_xml(el, n))


        b64 = pages_b64[m]

        page_xml = f"""
        <dict>
    		<key>currentImage</key>
    		<dict>
    			<key>datum</key>
    			<date>2024-10-28T14:48:37Z</date>
    			<key>ident</key>
    			<integer>{generate_ident()}</integer>
    			<key>image</key>
    			<string>{b64}</string>
    			<key>md5</key>
    			<string>b75bc6059ca9928d7170c3c227e91558</string>
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

        seite_liste.append(page_xml)


    frame_xml = f"""
    <?xml version="1.0" encoding="UTF-8"?>
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
		  {''.join(seite_liste)}
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
	<integer>{len(seite_liste)}</integer>
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

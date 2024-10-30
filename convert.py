import random
import ocr
import split_pdf
import shutil
import os
import pdf_to_b64
from klassen import Ankreuzfeld, Textfled, Feld

global_counter = 0

def generate_18_digit_uuid():
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
       	<integer>{generate_18_digit_uuid()}</integer>
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
       	<integer>{generate_18_digit_uuid()}</integer>
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

def convert(pdf_file_path: str):
    global global_counter
    global_counter = 0

    pages = split_pdf.pdf_to_png(pdf_file_path)

    pages_b64 = pdf_to_b64.pdf_to_base64_pages(pdf_file_path)

    seite_liste: list = []

    for m, page in enumerate(pages):

        arr_ankreuzfelder_rund_koord = ocr.runde_ankreuzfelder(page)
        arr_ankreuzfelder_quadratisch_koord = ocr.quadratische_ankreuzfelder(page)
        arr_textfelder_koord = ocr.textfelder(page)

        arr_felder = []
        arr_felder.extend(arr_ankreuzfelder_rund_koord)
        arr_felder.extend(arr_ankreuzfelder_quadratisch_koord)
        arr_felder.extend(arr_textfelder_koord)
        arr_felder.sort(key=lambda pos: ( int(pos.y_in_mm), int(pos.x_in_mm)))

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
    			<integer>{generate_18_digit_uuid()}</integer>
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
    		<integer>{generate_18_digit_uuid()}</integer>
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
	<integer>162560870423986178</integer>
	<key>kategorie</key>
	<string>Custom-Formulare</string>
	<key>kuerzel</key>
	<string>OCR</string>
	<key>listenposition</key>
	<integer>2</integer>
	<key>name</key>
	<string>CustomFormular_173892287</string>
	<key>numberOfDirectPages</key>
	<integer>{len(seite_liste)}</integer>
	<key>papersize_height</key>
	<real>840</real>
	<key>papersize_width</key>
	<real>595</real>
	<key>tooltip</key>
	<string>OCR</string>
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

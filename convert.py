import random
import ocr
import split_pdf
import shutil
import os
import pdf_to_b64

def generate_18_digit_uuid():
    return str(random.randint(10**17, 10**18 - 1))

def delete_folder(folder_name):
    # Überprüfen, ob der Ordner existiert
    if os.path.exists(folder_name) and os.path.isdir(folder_name):
        try:
            shutil.rmtree(folder_name)
            print(f"Ordner '{folder_name}' wurde erfolgreich gelöscht.")
        except Exception as e:
            print(f"Fehler beim Löschen des Ordners '{folder_name}': {e}")
    else:
        print(f"Ordner '{folder_name}' existiert nicht.")

def convert(pdf_file_path):
    # pdf_file_path = 'Beispiel.pdf'

    pages = split_pdf.pdf_to_png(pdf_file_path)
    # pages = ['image1.jpeg', 'image2.jpeg']

    pages_b64 = pdf_to_b64.pdf_to_base64_pages(pdf_file_path)

    seite_liste: list = []

    global_counter = 0

    for m, page in enumerate(pages):

        arr_ankreuzfelder_koord = ocr.runde_ankreuzfelder(page)
        arr_ankreuzfelder_koord.extend(ocr.quadratische_ankreuzfelder(page))
        arr_ankreuzfelder_xml: list = []
        for n, el in enumerate(arr_ankreuzfelder_koord):
            global_counter += 1
            name = f"v{global_counter}"
            width = 4.8038711547851562
            height = 6

            ankreuzfeld_xml = f"""
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
           	<real>{el[0] - width / 2}</real>
           	<key>ypos</key>
           	<real>{el[1] - height / 2}</real>
            </dict>"""

            arr_ankreuzfelder_xml.append(ankreuzfeld_xml)

        arr_textfelder_koord = ocr.horizontale_linien(page)
        arr_textfelder_xml: list = []
        for n, el in enumerate(arr_textfelder_koord):
            global_counter += 1
            name = f"v{global_counter}"
            x = el[0]
            y = el[1] - 5 # bisschen höher, ne?
            width = el[2]
            textfeld_xml = f"""
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

            arr_textfelder_xml.append(textfeld_xml)

        b64 = pages_b64[m]

        page_xml = f"""<dict>
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
			    {''.join(arr_ankreuzfelder_xml)}
				{''.join(arr_textfelder_xml)}
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

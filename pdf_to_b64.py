import fitz  # PyMuPDF
import base64
from io import BytesIO
from PIL import Image

def pdf_to_base64_pages(pdf_path):
    # Laden der PDF-Datei
    document = fitz.open(pdf_path)
    base64_pages = []

    # Für jede Seite im Dokument
    for page_num in range(len(document)):
        print(f"converting page {page_num} to b64.")
        page = document.load_page(page_num)

        # Rendern der Seite als Bild (200 DPI für gute Qualität)
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Bild in ByteIO umwandeln und als PNG speichern
        buffered = BytesIO()
        img.save(buffered, format="PNG")

        # Bild in Base64 konvertieren
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_pages.append(img_b64)

    # Dokument schließen
    document.close()

    return base64_pages

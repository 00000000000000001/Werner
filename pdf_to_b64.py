from pdf2image import convert_from_path
import base64
from io import BytesIO
from PIL import Image

def pdf_to_base64_pages(pdf_path):
    # Konvertiere jede PDF-Seite in ein Bild
    pages = convert_from_path(pdf_path, dpi=200)
    base64_pages = []

    # Für jede Seite im Bildformat
    for page_num, img in enumerate(pages):
        print(f"converting page {page_num} to b64.")

        # Bild in ByteIO umwandeln und als PNG speichern
        buffered = BytesIO()
        img.save(buffered, format="PNG")

        # Bild in Base64 konvertieren
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        base64_pages.append(img_b64)

    return base64_pages

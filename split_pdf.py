from pdf2image import convert_from_path
import os

def pdf_to_png(pdf_path, output_folder='output_images', dpi=300):
    res = []
    # Erstelle den Ordner für die Ausgabebilder, falls er nicht existiert
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Konvertiere die PDF in eine Liste von Bildern (Seiten)
    images = convert_from_path(pdf_path, dpi=dpi)

    # Jede Seite als PNG abspeichern
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"page_{i+1}.png")
        image.save(image_path, 'PNG')
        print(f"Seite {i+1} gespeichert als {image_path}")
        res.append(image_path)
    return res

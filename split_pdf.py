from pdf2image import convert_from_path
import os

def split_pdf_into_png_files(pdf_path, output_folder='output_images', dpi=300, count_offset=0) -> list:
    res = []

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    images = convert_from_path(pdf_path, dpi=dpi)

    for i, image in enumerate(images):
        page_number = i+1+count_offset
        image_path = os.path.join(output_folder, f"page_{page_number}.png")
        image.save(image_path, 'PNG')
        print(f"Seite {page_number} gespeichert als {image_path}")
        res.append(image_path)
    return res

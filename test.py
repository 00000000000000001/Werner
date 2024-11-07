import cv2
import numpy as np
from pdf2image import convert_from_path
import random

# Definiere die Klasse Textfeld
class Feld:
    def __init__(self, x_in_mm, y_in_mm):
        self.x_in_mm = x_in_mm
        self.y_in_mm = y_in_mm

class Textfeld(Feld):
    def __init__(self, x_in_mm, y_in_mm, w_in_mm):
        super().__init__(x_in_mm, y_in_mm)
        self.w_in_mm = w_in_mm

    def __repr__(self):
        return f"Textfeld(x: {self.x_in_mm} mm, y: {self.y_in_mm} mm, w: {self.w_in_mm} mm)"

def pdf_to_png(pdf_path):
    # Konvertiert eine PDF-Datei in eine Liste von PNG-Bildern
    images = convert_from_path(pdf_path, dpi=400)  # Höhere DPI für mehr Details
    png_images = []
    for i, image in enumerate(images):
        png_path = f'page_{i + 1}.png'
        image.save(png_path, 'PNG')
        png_images.append(png_path)
    return png_images

def detect_small_filled_circles(image_path):
    # Liest das Bild ein und wandelt es in Graustufen um
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Wendet einen adaptiven Schwellenwert an, um kleine, helle Punkte zu finden
    _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

    # Findet Konturen (kleine, gefüllte Kreise)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Liste für die Koordinaten der erkannten Punkte
    detected_points = []
    for contour in contours:
        # Berechnet die Umrandung und den Bereich der Kontur
        ((x, y), radius) = cv2.minEnclosingCircle(contour)
        area = cv2.contourArea(contour)

        # Bedingung für kleine, gefüllte Kreise (Punkte)
        if area > 5 and radius < 5:  # Anpassung der Größe für kleine Punkte
            detected_points.append((int(x), int(y)))

    return detected_points

def group_points_by_y(points, tolerance=3):
    # Sortiert die Punkte basierend auf der y-Koordinate
    points.sort(key=lambda p: p[1])

    # Liste für die gruppierten Punkte
    grouped_points = []

    # Aktuelle Gruppe initialisieren
    current_group = []
    current_y = None

    for point in points:
        x, y = point

        # Wenn noch keine Gruppe existiert, initialisiere die erste Gruppe
        if current_y is None:
            current_y = y
            current_group.append(point)

        # Prüft, ob der Punkt innerhalb der Toleranz zur aktuellen y-Koordinate liegt
        elif abs(y - current_y) <= tolerance:
            current_group.append(point)

        else:
            # Wenn der Punkt außerhalb der Toleranz liegt, speichere die aktuelle Gruppe und starte eine neue
            grouped_points.append(current_group)
            current_group = [point]
            current_y = y

    # Fügt die letzte Gruppe hinzu, falls sie nicht leer ist
    if current_group:
        grouped_points.append(current_group)

    return grouped_points

def split_groups_by_x_distance(groups, distance_threshold=50):
    new_groups = []

    for group in groups:
        # Sortiere die Gruppe nach x-Koordinate
        group.sort(key=lambda p: p[0])

        current_subgroup = [group[0]]  # Beginne mit dem ersten Punkt in einer neuen Untergruppe

        # Durchlaufe die Punkte und prüfe den Abstand zum nächsten
        for i in range(1, len(group)):
            x1, y1 = group[i - 1]
            x2, y2 = group[i]

            # Prüfe, ob der Abstand in x-Richtung größer ist als der Schwellenwert
            if abs(x2 - x1) > distance_threshold:
                # Falls ja, füge die aktuelle Untergruppe als neue Gruppe hinzu
                new_groups.append(current_subgroup)
                current_subgroup = [group[i]]  # Starte eine neue Untergruppe
            else:
                current_subgroup.append(group[i])  # Füge den Punkt zur aktuellen Untergruppe hinzu

        # Füge die letzte Untergruppe hinzu, wenn sie nicht leer ist
        if current_subgroup:
            new_groups.append(current_subgroup)

    return new_groups

def convert_groups_to_textfields(groups):
    # Wandelt jede Gruppe in ein Textfeld um
    textfields = []
    for group in groups:
        # Bestimme die minimale und maximale x-Koordinate sowie die mittlere y-Koordinate
        min_x = min(point[0] for point in group)
        max_x = max(point[0] for point in group)
        y_mean = int(sum(point[1] for point in group) / len(group))

        # Berechne die Breite und die Koordinaten in mm (angenommene Umrechnung von Pixel zu mm)
        x_in_mm = min_x * 0.264583  # Beispielhafte Umrechnung, abhängig von DPI
        y_in_mm = y_mean * 0.264583
        w_in_mm = (max_x - min_x) * 0.264583

        # Erstelle ein Textfeld und füge es zur Liste hinzu
        textfields.append(Textfeld(x_in_mm, y_in_mm, w_in_mm))

    return textfields

# Beispiel: PDF in PNG konvertieren und nach Punkten suchen
pdf_path = 'test/Beispiel_2.pdf'
png_images = pdf_to_png(pdf_path)

# Durchläuft alle PNG-Bilder und sucht nach kleinen, gefüllten Kreisen
for png_image in png_images:
    print(f"Untersuche {png_image}...")
    points = detect_small_filled_circles(png_image)

    if points:
        # Gruppiert die Punkte nach y-Koordinate
        grouped_points = group_points_by_y(points)
        # Splitte die Gruppen basierend auf Abstand in x-Richtung
        split_groups = split_groups_by_x_distance(grouped_points)
        # Filtert Gruppen mit weniger als 5 Punkten aus
        filtered_groups = [group for group in split_groups if len(group) >= 5]

        # Wandle die gefilterten Gruppen in Textfelder um
        textfields = convert_groups_to_textfields(filtered_groups)

        if textfields:
            print(f"Gefundene Textfelder: {textfields}")
        else:
            print("Keine gültigen Textfelder gefunden.")
    else:
        print("Keine Punkte gefunden.")

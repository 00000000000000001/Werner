import cv2
import numpy as np
# import matplotlib.pyplot as plt
from klassen import Ankreuzfeld, Textfled

def quadratische_ankreuzfelder(image_path: str, bildbreite_mm=210, bildhoehe_mm=297) -> list:
    res = []
    detected_centers = []  # Liste zum Speichern der Mittelpunkte bereits erkannter Quadrate

    # Bild laden
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Bild konnte nicht geladen werden. Überprüfen Sie den Pfad.")

    # Bild in Graustufen umwandeln
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Sanften adaptiven Schwellenwert anwenden, um nur wichtige Unterschiede hervorzuheben
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 11, 2)

    # Leichte Erosion und Dilatation, um kleine Ränder zu entfernen, die verschmolzene Kanten verursachen können
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Konturen finden und Hierarchie abrufen
    contours, hierarchy = cv2.findContours(morphed, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Mindestgröße und Maximalgröße für Quadrate/Rechtecke festlegen (z.B. 20x20 bis 100x100 Pixel)
    min_size = 20
    max_size = 100

    # Bildabmessungen in Pixel
    image_height_px, image_width_px = gray.shape

    # Berechnung der mm pro Pixel
    mm_per_pixel_x = bildbreite_mm / image_width_px
    mm_per_pixel_y = bildhoehe_mm / image_height_px

    # Schleife über die gefundenen Konturen
    for i, contour in enumerate(contours):
        # Überprüfen, ob die Kontur eine äußere oder innere Kontur ist
        if hierarchy[0][i][3] == -1 or hierarchy[0][i][3] != -1:
            # Kontur approximieren (vereinfachen)
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Wenn die approximierte Kontur 4 Ecken hat, handelt es sich um ein Rechteck oder Quadrat
            if len(approx) == 4:
                # Kontrollieren, ob es ein Rechteck oder Quadrat ist (Seitenverhältnis prüfen)
                (x, y, w, h) = cv2.boundingRect(approx)
                aspect_ratio = w / float(h)

                # Toleranz für das Seitenverhältnis erweitern, z.B. erlauben wir jetzt 0.75 bis 1.33
                if 0.75 <= aspect_ratio <= 1.33 and min_size <= w <= max_size and min_size <= h <= max_size:
                    # Mittelpunkt des Rechtecks berechnen
                    center_x = x + w // 2
                    center_y = y + h // 2

                    # Überprüfen, ob dieser Mittelpunkt nahe an einem bereits erkannten Quadrat liegt
                    duplicate = False
                    for (detected_x, detected_y) in detected_centers:
                        if abs(center_x - detected_x) < 10 and abs(center_y - detected_y) < 10:
                            duplicate = True
                            break

                    # Wenn kein Duplikat gefunden wurde, Quadrat speichern und markieren
                    if not duplicate:
                        detected_centers.append((center_x, center_y))  # Hinzufügen des neuen Mittelpunkts
                        center_x_mm = center_x * mm_per_pixel_x
                        center_y_mm = center_y * mm_per_pixel_y
                        res.append(Ankreuzfeld(center_x_mm, center_y_mm))

                        # Quadrat oder Rechteck zeichnen und Mittelpunkt markieren (optional)
                        # cv2.drawContours(image, [approx], -1, (0, 255, 0), 3)
                        # cv2.circle(image, (center_x, center_y), 5, (0, 0, 255), -1)

    # Sortieren der Quadrate: zuerst nach y, dann nach x
    res.sort(key=lambda pos: (pos.y_in_mm, pos.x_in_mm))

    return res

def runde_ankreuzfelder(pfad_zur_datei, bildbreite_mm=210, bildhoehe_mm=297, min_radius_px=15, max_radius_px=25, umgebung_puffer_px=10):
    # Bild in Graustufen laden und Kanten hervorheben
    bild = cv2.imread(pfad_zur_datei, cv2.IMREAD_GRAYSCALE)
    bild_hoehe, bild_breite = bild.shape[:2]

    # Berechnung der Skalierungsfaktoren in mm pro Pixel basierend auf DIN-A4-Maßen
    mm_pro_pixel_breite = bildbreite_mm / bild_breite
    mm_pro_pixel_hoehe = bildhoehe_mm / bild_hoehe

    # Binärschwellenwert anwenden, um das Bild für die Konturenerkennung vorzubereiten
    _, thresh = cv2.threshold(bild, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Konturen finden
    konturen, hierarchie = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Ergebnis-Liste für Mittelpunkte der "perfekten" Kreise in mm initialisieren
    perfekte_kreise_mm = []

    # Parameter für Kreiserkennung
    epsilon_formfaktor = 0.2  # Toleranz für den Formfaktor
    epsilon_aspektverhältnis = 0.1  # Toleranz für das Verhältnis von Höhe zu Breite

    for i, kontur in enumerate(konturen):
        # Überspringen, wenn die Kontur ein innerer Bereich (Loch) ist
        if hierarchie[0][i][3] != -1:
            continue  # Nur äußere Konturen berücksichtigen

        # Bounding-Box für Kontur berechnen
        x, y, breite, hoehe = cv2.boundingRect(kontur)

        # Aspektverhältnis überprüfen (breite / höhe nahe 1)
        aspektverhältnis = breite / float(hoehe)
        if abs(1 - aspektverhältnis) > epsilon_aspektverhältnis:
            continue  # Falls oval, überspringen

        # Fläche berechnen und überprüfen, ob sie größer als 0 ist
        flaeche = cv2.contourArea(kontur)
        if flaeche == 0:
            continue  # Falls Fläche null ist, überspringen

        # Formfaktor überprüfen
        umfang = cv2.arcLength(kontur, True)
        formfaktor = (umfang ** 2) / (4 * np.pi * flaeche)
        if abs(1 - formfaktor) > epsilon_formfaktor:
            continue  # Falls kein perfekter Kreis, überspringen

        # Berechnung des umschreibenden Kreises und Radius überprüfen
        (cx_pixel, cy_pixel), radius = cv2.minEnclosingCircle(kontur)
        if not (min_radius_px <= radius <= max_radius_px):
            continue  # Falls der Radius nicht innerhalb der Grenzen liegt, überspringen

        # Konvexität prüfen
        hull = cv2.convexHull(kontur)
        hull_area = cv2.contourArea(hull)
        solidity = flaeche / hull_area if hull_area > 0 else 0
        if solidity < 0.9:  # Ein Kreis hat eine hohe Konvexität, typischerweise nahe 1
            continue

        # Überprüfung auf umliegende Konturen (Umgebungs-Check)
        umgebungsbereich = thresh[max(0, y - umgebung_puffer_px): min(bild_hoehe, y + hoehe + umgebung_puffer_px),
                                  max(0, x - umgebung_puffer_px): min(bild_breite, x + breite + umgebung_puffer_px)]
        umgebende_konturen, _ = cv2.findContours(umgebungsbereich, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Prüfen, ob umliegende Konturen (außerhalb der aktuellen Kontur) gefunden wurden
        if len(umgebende_konturen) > 1:  # Mehr als 1 bedeutet, dass andere Konturen in der Umgebung liegen
            continue  # Überspringen, da wahrscheinlich ein "O" in einem Wort

        # Umrechnung der Pixel-Koordinaten in mm
        cx_mm = cx_pixel * mm_pro_pixel_breite
        cy_mm = cy_pixel * mm_pro_pixel_hoehe
        perfekte_kreise_mm.append(Ankreuzfeld(cx_mm, cy_mm))

    # Sortieren der Kreise: zuerst nach y, dann nach x
    # perfekte_kreise_mm.sort(key=lambda pos: (pos.x_in_mm, pos.y_in_mm))

    return perfekte_kreise_mm

def textfelder(image_path: str, bildbreite_mm=210, bildhoehe_mm=297) -> list:
    # Bild in Graustufen laden
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError("Bild konnte nicht geladen werden. Überprüfen Sie den Pfad.")

    # Binarisierung, um nur Schwarz-Weiß-Pixel zu erhalten
    _, binary = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY_INV)

    # Horizontalen Strukturkern erstellen und horizontale Linien extrahieren
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)

    # Vertikalen Strukturkern erstellen und vertikale Linien extrahieren
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    # Subtrahieren der vertikalen Linien von den horizontalen Linien
    isolated_horizontal_lines = cv2.subtract(horizontal_lines, vertical_lines)

    # Konturen der isolierten horizontalen Linien finden
    contours, _ = cv2.findContours(isolated_horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Bildabmessungen in Pixel
    image_height_px, image_width_px = image.shape

    # Berechnung der mm pro Pixel
    pixel_to_mm_x = bildbreite_mm / image_width_px
    pixel_to_mm_y = bildhoehe_mm / image_height_px

    # Filter für isolierte Linien: Breite, Höhe und Isolation prüfen
    lines_positions_mm = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Überprüfen der Breite und Höhe (Linienverhältnis)
        if w > 200 and h < 20:  # Optional: Breite und Höhe anpassen
            # Prüfen, ob die Linie links oder rechts in direkter Nähe an vertikale Linien grenzt
            padding = 5  # Abstand, um die Nähe zu vertikalen Linien zu prüfen

            # Bereich links und rechts der Linie extrahieren
            left_area = vertical_lines[y:y+h, max(0, x-padding):x]
            right_area = vertical_lines[y:y+h, x+w:min(x+w+padding, vertical_lines.shape[1])]

            # Prüfen, ob keine vertikalen Linien direkt daneben vorhanden sind
            if not (np.any(left_area) or np.any(right_area)):
                # Umrechnung der Koordinaten und Größe von Pixeln in Millimeter
                x_mm = x * pixel_to_mm_x
                y_mm = y * pixel_to_mm_y
                w_mm = w * pixel_to_mm_x
                lines_positions_mm.append(Textfled(x_mm, y_mm, w_mm))

    # Sortieren der Linien: zuerst nach y, dann nach x
    lines_positions_mm.sort(key=lambda pos: (pos.y_in_mm, pos.x_in_mm))

    return lines_positions_mm

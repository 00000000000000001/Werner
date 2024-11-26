import cv2
import math
from klassen import Ankreuzfeld, Rechteck, Textfeld
import pytesseract

def erkenne_kleine_rechtecke(image_path: str, bildbreite_mm=210, bildhoehe_mm=297, min_size=10, max_size=100) -> list:
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

    # Bildabmessungen in Pixel
    image_height_px, image_width_px = gray.shape

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

                        # Füge ein Ankreuzfeld mit den Eckenkoordinaten hinzu
                        res.append(Ankreuzfeld(x, y, (x + w), (y + h)).to_mm())

    # Sortieren der Quadrate: zuerst nach y, dann nach x
    res.sort(key=lambda pos: (pos.y1, pos.x1))

    return res

def erkenne_kleine_kreise(pfad_zur_datei, bildbreite_mm=210, bildhoehe_mm=297, min_radius_px=5, max_radius_px=50, umgebung_puffer_px=10):
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

    # Ergebnis-Liste für die erkannten Kreise als Ankreuzfelder initialisieren
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
        formfaktor = (umfang ** 2) / (4 * math.pi * flaeche)
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

        # Ankreuzfeld mit den Eckenkoordinaten erstellen und zur Liste hinzufügen
        perfekte_kreise_mm.append(Ankreuzfeld(x, y, (x + breite), (y + hoehe)).to_mm())

    return perfekte_kreise_mm

def erkenne_linien(image_path: str, bildbreite_mm=210, bildhoehe_mm=297, min_width=50, dpi=300) -> list[Textfeld]:
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

    # Filter für isolierte Linien: Breite, Höhe und Isolation prüfen
    lines_positions_mm = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # Überprüfen der Breite und Höhe (Linienverhältnis)
        if w > min_width and h < 20:  # Optional: Breite und Höhe anpassen
            # Prüfen, ob die Linie links oder rechts in direkter Nähe an vertikale Linien grenzt
            padding = 5  # Abstand, um die Nähe zu vertikalen Linien zu prüfen

            # Bereich links und rechts der Linie extrahieren
            left_area = vertical_lines[y:y+h, max(0, x-padding):x]
            right_area = vertical_lines[y:y+h, x+w:min(x+w+padding, vertical_lines.shape[1])]

            # Prüfen, ob keine vertikalen Linien direkt daneben vorhanden sind
            if not (cv2.countNonZero(left_area) > 0 or cv2.countNonZero(right_area) > 0):

                pxl_pro_mm = dpi / 25.4

                # Hinzufügen eines Textfeld-Objekts mit den beiden Ecken
                lines_positions_mm.append(Textfeld(x, y - 5 * pxl_pro_mm, (x + w), y + 1 * pxl_pro_mm).to_mm())

    # Sortieren der Linien: zuerst nach y, dann nach x
    lines_positions_mm.sort(key=lambda pos: (pos.y1, pos.x1))

    return lines_positions_mm

def erkenne_linien_gepunktet(image_path: str, bildbreite_mm=210, bildhoehe_mm=297, distance_threshold=20) -> list[Textfeld]:

    def detect_small_filled_circles(image_path):
        image = cv2.imread(image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Schwellenwert zur Binarisierung anpassen
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)

        # Tabellenstruktur entfernen
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        binary_no_table = cv2.subtract(binary, table_structure)

        # Suche nach kleinen, gefüllten Kreisen
        contours, _ = cv2.findContours(binary_no_table, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detected_points = []
        for contour in contours:
            ((x, y), radius) = cv2.minEnclosingCircle(contour)
            area = cv2.contourArea(contour)
            if area > 3 and radius < 6:  # Angepasste Werte für besseren Radius
                detected_points.append((int(x), int(y)))
        return detected_points

    def group_points_by_y(points, tolerance=5):  # Toleranz angepasst
        points.sort(key=lambda p: p[1])
        grouped_points, current_group, current_y = [], [], None
        for point in points:
            x, y = point
            if current_y is None or abs(y - current_y) <= tolerance:
                current_group.append(point)
            else:
                grouped_points.append(current_group)
                current_group = [point]
            current_y = y
        if current_group:
            grouped_points.append(current_group)
        return grouped_points

    def split_groups_by_x_distance(groups):
        new_groups = []
        for group in groups:
            group.sort(key=lambda p: p[0])
            current_subgroup = [group[0]]
            for i in range(1, len(group)):
                x1, y1 = group[i - 1]
                x2, y2 = group[i]
                if abs(x2 - x1) > distance_threshold:
                    new_groups.append(current_subgroup)
                    current_subgroup = [group[i]]
                else:
                    current_subgroup.append(group[i])
            if current_subgroup:
                new_groups.append(current_subgroup)
        return new_groups

    def convert_groups_to_textfields(groups, img_width_px, img_height_px, bildbreite_mm, bildhoehe_mm):
        textfields = []
        px_to_mm_x = bildbreite_mm / img_width_px
        px_to_mm_y = bildhoehe_mm / img_height_px
        for group in groups:
            if len(group) < 5:
                continue
            min_x = min(point[0] for point in group)
            max_x = max(point[0] for point in group)
            min_y = min(point[1] for point in group)
            max_y = max(point[1] for point in group)

            # Umrechnung der Koordinaten von Pixel in Millimeter
            x1_mm = min_x * px_to_mm_x
            y1_mm = min_y * px_to_mm_y
            x2_mm = max_x * px_to_mm_x
            y2_mm = max_y * px_to_mm_y

            # Hinzufügen eines Textfeld-Objekts mit den Eckenkoordinaten
            textfields.append(Textfeld(x1_mm, y1_mm - 5, x2_mm, y1_mm + 1))
        return textfields

    # Bild laden, um Bilddimensionen in Pixeln zu ermitteln
    image = cv2.imread(image_path)
    img_height_px, img_width_px = image.shape[:2]

    # Schritte der Bildverarbeitung
    points = detect_small_filled_circles(image_path)
    if not points:
        return []
    grouped_points = group_points_by_y(points)
    split_groups = split_groups_by_x_distance(grouped_points)
    textfields = convert_groups_to_textfields(split_groups, img_width_px, img_height_px, bildbreite_mm, bildhoehe_mm)
    return textfields

def erkenne_zellen(pfad_zum_bild, dpi=300, min_breite_mm=5, min_hoehe_mm=5, padding_mm=0.5):

    def entferne_tabellenlinien(bild):
        graubild = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)

        # Adaptive Schwellenwertsetzung
        adaptives_binarisiert = cv2.adaptiveThreshold(graubild, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                      cv2.THRESH_BINARY_INV, 15, 9)

        # Morphologische Operationen zur Linienentfernung
        kernel_horizontal = cv2.getStructuringElement(cv2.MORPH_RECT, (bild.shape[1] // 40, 1))
        horizontale_linien = cv2.morphologyEx(adaptives_binarisiert, cv2.MORPH_OPEN, kernel_horizontal)

        kernel_vertical = cv2.getStructuringElement(cv2.MORPH_RECT, (1, bild.shape[0] // 40))
        vertikale_linien = cv2.morphologyEx(adaptives_binarisiert, cv2.MORPH_OPEN, kernel_vertical)

        linien = cv2.add(horizontale_linien, vertikale_linien)
        ohne_linien = cv2.subtract(adaptives_binarisiert, linien)

        # Erosion und Dilation anwenden
        kernel_erode_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        ohne_linien = cv2.erode(ohne_linien, kernel_erode_dilate, iterations=1)
        ohne_linien = cv2.dilate(ohne_linien, kernel_erode_dilate, iterations=1)

        return ohne_linien

    def erkenne_text_und_rahmen(pfad_zum_bild, dpi=300):
        bild = cv2.imread(pfad_zum_bild)
        if bild is None:
            raise FileNotFoundError(f"Bilddatei {pfad_zum_bild} nicht gefunden.")

        # Vorverarbeitung: Entfernen der Tabellenlinien
        vorverarbeitetes_bild = entferne_tabellenlinien(bild)

        # OCR-Analyse mit optimierten Parametern
        ocr_config = '--psm 6'  # psm 6 ist gut für tabellarische Daten
        daten = pytesseract.image_to_data(vorverarbeitetes_bild, output_type=pytesseract.Output.DICT, config=ocr_config)
        textbloecke = []

        # Textblöcke erkennen und speichern
        for i in range(len(daten['text'])):
            text = daten['text'][i].strip()
            if not text or text in {"O", "o", "0", "ö"}:
                continue

            x1_pixel = daten['left'][i]
            y1_pixel = daten['top'][i]
            breite_pixel = daten['width'][i]
            hoehe_pixel = daten['height'][i]

            x2_pixel = x1_pixel + breite_pixel
            y2_pixel = y1_pixel + hoehe_pixel

            textbloecke.append(Textfeld(x1_pixel, y1_pixel, x2_pixel, y2_pixel, dpi=dpi))

            # Rechteck auf das Bild zeichnen
            cv2.rectangle(bild, (x1_pixel, y1_pixel), (x2_pixel, y2_pixel), (0, 255, 0), 2)
            cv2.putText(bild, text, (x1_pixel, y1_pixel - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Bild mit markierten Textblöcken anzeigen
        # cv2.imshow("Bild mit erkannten Textblöcken", bild)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        return textbloecke

    bild = cv2.imread(pfad_zum_bild)
    if bild is None:
        raise FileNotFoundError(f"Bilddatei {pfad_zum_bild} nicht gefunden.")

    graubild = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)
    _, binarisiert = cv2.threshold(graubild, 127, 255, cv2.THRESH_BINARY_INV)
    konturen, _ = cv2.findContours(binarisiert, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    pixel_pro_mm = dpi / 25.4
    min_breite_pixel = int(min_breite_mm * pixel_pro_mm)
    min_hoehe_pixel = int(min_hoehe_mm * pixel_pro_mm)
    padding_pixel = int(padding_mm * pixel_pro_mm)

    textfelder = []
    for kontur in konturen:
        x, y, breite, hoehe = cv2.boundingRect(kontur)

        if breite >= min_breite_pixel and hoehe >= min_hoehe_pixel:
            x += padding_pixel
            y += padding_pixel
            breite -= 2 * padding_pixel
            hoehe -= 2 * padding_pixel

            x2 = x + breite
            y2 = y + hoehe

            textfelder.append(Textfeld(x, y, x2, y2, dpi=dpi))

    gefilterte_textfelder = []
    for i, tf1 in enumerate(textfelder):
        ueberdeckt = False
        for j, tf2 in enumerate(textfelder):
            if i != j:
                if (tf1.x1 <= tf2.x1 and tf1.y1 <= tf2.y1 and
                    tf1.x2 >= tf2.x2 and tf1.y2 >= tf2.y2):
                    ueberdeckt = True
                    break
        if not ueberdeckt:
            gefilterte_textfelder.append(tf1)

    finale_textfelder = []
    textbloecke = erkenne_text_und_rahmen(pfad_zum_bild, dpi=dpi)

    for tf in gefilterte_textfelder:
        ueberdeckt = False
        for tb in textbloecke:
            if (tf.x1 < tb.x2 and tf.x2 > tb.x1 and
                tf.y1 < tb.y2 and tf.y2 > tb.y1):
                ueberdeckt = True
                break
        if not ueberdeckt:
            finale_textfelder.append(tf)

    # Konvertiere finale Textfelder in mm falls benötigt
    finale_textfelder_mm = [tf.to_mm() for tf in finale_textfelder]
    return finale_textfelder_mm

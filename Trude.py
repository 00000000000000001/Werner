from utils import mm_to_pixel
import json
from Klassen import Ankreuzfeld, Textfeld, Punkt
from pdf2image import convert_from_path
import random
from Formular import Formular
import cv2
import numpy as np
import uuid
from typing import List, Tuple
from PIL import Image
import math
import os
from pathlib import Path

def prepare_image(pil_image, dilation_kernel_size: Tuple[int, int] = (3, 3)):
    # Konvertierung von PIL nach OpenCV
    img_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

    # Adaptive Schwellenwertbildung
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Morphologische Operation
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilation_kernel_size)
    morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    return morphed

def rechtecke_erkennen(
    pil_image: Image.Image,
    min_height: float = 10.,
    min_width: float = 75.,
    max_height: float = 2000.,
    max_width: float = 2000.,
    approx_epsilon_factor: float = 0.02,
    dilation_kernel_size: Tuple[int, int] = (3, 3),
    center_tolerance: int = 10
) -> List[Tuple[Punkt, Punkt]]:

        """
        Erkennt rechteckige Zellen in einem gegebenen PIL-Bildobjekt anhand von Konturen-
        und Größenkriterien. Die Breite und Höhe der Zellen werden in Pixeln angegeben.

        Parameter
        ---------
        pil_image : Image.Image
            Das Eingangsbild als PIL-Image.
        min_height : float
            Minimale akzeptierte Höhe einer Zelle in Pixeln.
        min_width : float
            Minimale akzeptierte Breite einer Zelle in Pixeln.
        max_height : float
            Maximale akzeptierte Höhe einer Zelle in Pixeln.
        max_width : float
            Maximale akzeptierte Breite einer Zelle in Pixeln.
        approx_epsilon_factor : float
            Faktor für die Polygonapproximation. Standardwert 0.02.
        dilation_kernel_size : Tuple[int, int]
            Kernelgröße für die morphologische Operation. Standardwert (3, 3).
        center_tolerance : int
            Toleranz in Pixeln für das Erkennen bereits detektierter Zellen, um Duplikate zu vermeiden.

        Returns
        -------
        List[Textfeld]
            Liste der gefundenen Zellen als `Textfeld`-Objekte.
        """

        # Konturen finden
        contours, hierarchy = cv2.findContours(pil_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        rechtecke = []
        detected_centers = []

        for i, contour in enumerate(contours):

            # Polygonapproximation
            epsilon = approx_epsilon_factor * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Rechtecke haben 4 Ecken
            if len(approx) == 4:
                (x, y, w, h) = cv2.boundingRect(approx)

                # Überprüfe Mindest- und Maximalmaße
                if (h >= min_height and h <= max_height and
                    w >= min_width and w <= max_width):
                    center_x = x + w // 2
                    center_y = y + h // 2

                    # Überprüfe auf Duplikate
                    if not any(abs(center_x - dx) < center_tolerance and abs(center_y - dy) < center_tolerance
                               for dx, dy in detected_centers):
                        detected_centers.append((center_x, center_y))
                        rechtecke.append( (Punkt(x=x, y=y), Punkt(x=x+w, y=y+h)) )

        return rechtecke

def kaestchen_erkennen(
    pil_image: Image.Image,
    min_height: float = 15.,
    min_width: float = 15.,
    max_height: float = 100.,
    max_width: float = 100.,
    approx_epsilon_factor: float = 0.02,
    dilation_kernel_size: Tuple[int, int] = (3, 3),
    center_tolerance: int = 10,
    dpi: int = 300
) -> List[Ankreuzfeld]:

    # 1 mm = dpi / 25.4 Pixel
    mm_to_px = lambda mm: mm * dpi / 25.4
    min_width_mm_px = mm_to_px(5)
    min_height_mm_px = mm_to_px(5)

    # Rechtecke erkennen (gibt bereits Ankreuzfeld-Objekte zurück)
    kaestchen = rechtecke_erkennen(
        prepare_image(pil_image),
        min_height, min_width,
        max_height, max_width,
        approx_epsilon_factor,
        dilation_kernel_size,
        center_tolerance
    )

    ankreuzfelder = []
    for feld in kaestchen:
        # Koordinaten extrahieren
        x1, y1 = feld[0].x, feld[0].y
        x2, y2 = feld[1].x, feld[1].y

        # Breite und Höhe immer als positive Werte berechnen
        width = x2 - x1
        height = y2 - y1

        # Mindestbreite sicherstellen
        if width < min_width_mm_px:
            diff_w = min_width_mm_px - width
            x1 -= diff_w / 2  # Links erweitern
            x2 += diff_w / 2  # Rechts erweitern

        # Mindesthöhe sicherstellen
        if height < min_height_mm_px:
            diff_h = min_height_mm_px - height
            y1 -= diff_h / 2  # Oben erweitern
            y2 += diff_h / 2  # Unten erweitern

        # Neues, angepasstes Ankreuzfeld erstellen
        neues_feld = Ankreuzfeld(Punkt(x1, y1), Punkt(x2, y2))
        ankreuzfelder.append(neues_feld)

    return ankreuzfelder

def zellen_erkennen(
    pil_image: Image.Image,
    min_height: float = 50.,
    min_width: float = 100.,
    max_height: float = float("inf"),
    max_width: float = float("inf"),
    approx_epsilon_factor: float = 0.02,
    dilation_kernel_size: Tuple[int, int] = (3, 3),
    center_tolerance: int = 10,
    padding: int = 10,
    max_perc_white_pixels: float = 0.01,
) -> List[Textfeld]:

    def percentage_of_white_pixels(pil_image: Image.Image, links_oben: Punkt, rechts_unten: Punkt, padding: int = 5) -> float:
        # Zuschneiden des interessierenden Bereichs mit reduziertem Rahmen
        x1 = max(links_oben.x + padding, 0)
        y1 = max(links_oben.y + padding, 0)
        x2 = max(rechts_unten.x - padding, 0)
        y2 = max(rechts_unten.y - padding, 0)

        # Sicherstellen, dass die Koordinaten gültig sind
        if x2 <= x1 or y2 <= y1:
            return 0.0

        cropped = pil_image[y1:y2, x1:x2]

        # Berechnung des Anteils weißer Pixel
        white_pixel_count = cv2.countNonZero(cropped)
        total_pixel_count = cropped.size

        # Prozentualer Anteil weißer Pixel
        return white_pixel_count / total_pixel_count if total_pixel_count > 0 else 0.0

    pil_image = prepare_image(pil_image)

    rechtecke = rechtecke_erkennen(
        pil_image, min_height, min_width, max_height, max_width, approx_epsilon_factor, dilation_kernel_size, center_tolerance
    )

    zellen = []

    for t in rechtecke:
        p = percentage_of_white_pixels(pil_image, t[0], t[1], padding=padding)
        # print(f"Prozent weißer Pixel: {p:.3f}")
        if p <= max_perc_white_pixels:
            zellen.append(Textfeld(Punkt(t[0].x+padding, t[0].y+padding), Punkt(t[1].x-padding, t[1].y-padding)))

    return zellen

def linien_erkennen(
    pil_image: Image.Image,
    min_width: float = 100.,
    dilation_kernel_size: Tuple[int, int] = (25, 1),
    dpi: int = 300
) -> List[Textfeld]:
    """
    Erkennt isolierte, rein horizontale Linien in einem Bild.

    Args:
        pil_image (Image.Image): Eingabebild als PIL Image.
        min_width (float): Minimale Breite der zu erkennenden Linien in Pixeln.
        dilation_kernel_size (Tuple[int, int], optional): Größe des Dilation-Kernels. Standard ist (25,1) für horizontale Linien.
        dpi (int, optional): DPI des Bildes für Konvertierungen.

    Returns:
        List[Textfeld]: Liste der erkannten Linien als Textfeld-Objekte.
    """
    # Konvertierung von PIL-Bild zu OpenCV-kompatiblem Format
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)

    # Binarisierung, um nur Schwarz-Weiß-Pixel zu erhalten
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Horizontalen Strukturkern erstellen und horizontale Linien extrahieren
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, dilation_kernel_size)
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)

    # Vertikalen Strukturkern erstellen und vertikale Linien extrahieren
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, dilation_kernel_size[0]))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)

    # Subtrahieren der vertikalen Linien von den horizontalen Linien
    isolated_horizontal_lines = cv2.subtract(horizontal_lines, vertical_lines)

    # Konturen der isolierten horizontalen Linien finden
    contours, _ = cv2.findContours(isolated_horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter für isolierte Linien: Breite, Höhe und Isolation prüfen
    textfelder = []
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
                # Hinzufügen eines Textfeld-Objekts mit den beiden Ecken
                textfelder.append(Textfeld(Punkt(x, y-mm_to_pixel(5, dpi)), Punkt(x + w, y + mm_to_pixel(1, dpi))))

    return textfelder

def kreise_erkennen(
    pil_image: Image.Image,
    min_radius: float = mm_to_pixel(1, 300),
    max_radius: float = mm_to_pixel(10, 300),
    umgebung_puffer: float = 10,
    epsilon_formfaktor: float = 0.2,
    epsilon_aspektverhaeltnis: float = 0.2,
    solidity_threshold: float = 0.9,
    dilation_kernel_size: Tuple[int, int] = (3, 3),
    dpi: int = 300
) -> List[Ankreuzfeld]:
    """
    Erkennt kreisförmige Konturen in einem gegebenen PIL-Bild anhand von Konturmerkmalen
    und stellt sicher, dass alle erkannten Kreise die Mindestgröße von 5x6 mm einhalten.

    Returns
    -------
    List[Ankreuzfeld]
        Liste der gefundenen kreisförmigen Ankreuzfelder in Pixeln.
    """

    # Mindestgröße in Pixel (5 mm x 6 mm)
    mm_to_px = lambda mm: mm * dpi / 25.4
    min_width_mm_px = mm_to_px(5)
    min_height_mm_px = mm_to_px(5)

    # Konvertiere PIL-Image in ein OpenCV-Bild
    img_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

    # Binärschwellenwert anwenden
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Konturen finden
    konturen, hierarchie = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    # Ergebnis-Liste für die erkannten Kreise initialisieren
    perfekte_kreise = []

    # Bildgröße abrufen
    bild_hoehe, bild_breite = gray.shape[:2]

    for i, kontur in enumerate(konturen):
        # Überspringen, wenn die Kontur ein innerer Bereich (Loch) ist
        if hierarchie[0][i][3] != -1:
            continue  # Nur äußere Konturen berücksichtigen

        # Bounding-Box für Kontur berechnen
        x, y, breite, hoehe = cv2.boundingRect(kontur)

        # Aspektverhältnis überprüfen (Breite / Höhe nahe 1)
        aspektverhaeltnis = breite / float(hoehe)
        if abs(1 - aspektverhaeltnis) > epsilon_aspektverhaeltnis:
            continue  # Falls oval, überspringen

        # Fläche berechnen und überprüfen
        flaeche = cv2.contourArea(kontur)
        if flaeche == 0:
            continue  # Falls Fläche null ist, überspringen

        # Formfaktor überprüfen
        umfang = cv2.arcLength(kontur, True)
        formfaktor = (umfang ** 2) / (4 * math.pi * flaeche)
        if abs(1 - formfaktor) > epsilon_formfaktor:
            continue  # Falls kein perfekter Kreis, überspringen

        # Umschreibenden Kreis und Radius berechnen
        (cx_pixel, cy_pixel), radius = cv2.minEnclosingCircle(kontur)
        if not (min_radius <= radius <= max_radius):
            continue  # Falls Radius nicht innerhalb der Grenzen liegt, überspringen

        # Konvexität prüfen
        hull = cv2.convexHull(kontur)
        hull_area = cv2.contourArea(hull)
        solidity = flaeche / hull_area if hull_area > 0 else 0
        if solidity < solidity_threshold:
            continue

        # Umgebungsprüfung
        umgebungsbereich = thresh[max(0, int(y - umgebung_puffer)): min(bild_hoehe, int(y + hoehe + umgebung_puffer)),
                                  max(0, int(x - umgebung_puffer)): min(bild_breite, int(x + breite + umgebung_puffer))]
        umgebende_konturen, _ = cv2.findContours(umgebungsbereich, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(umgebende_konturen) > 1:
            continue  # Falls es andere Konturen in der Umgebung gibt

        # Mindestgröße sicherstellen
        if breite < min_width_mm_px:
            diff_w = min_width_mm_px - breite
            x -= diff_w / 2  # Links erweitern
            breite += diff_w

        if hoehe < min_height_mm_px:
            diff_h = min_height_mm_px - hoehe
            y -= diff_h / 2  # Oben erweitern
            hoehe += diff_h

        # Hinzufügen zur Ergebnisliste
        perfekte_kreise.append(
            Ankreuzfeld(
                Punkt(x, y),
                Punkt(x + breite, y + hoehe)
            )
        )

    return perfekte_kreise

def detect_small_filled_circles(gray_image):
    # Schwellenwert zur Binarisierung anpassen
    _, binary = cv2.threshold(gray_image, 180, 255, cv2.THRESH_BINARY_INV)

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

def group_points_by_y(points, tolerance=5):
    points.sort(key=lambda p: p[1])  # Sortiere nach Y-Koordinate
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

def split_groups_by_x_distance(groups, distance_threshold):
    new_groups = []
    for group in groups:
        group.sort(key=lambda p: p[0])  # Sortiere nach X-Koordinate
        current_subgroup = [group[0]]
        for i in range(1, len(group)):
            x1, y1 = group[i - 1]
            x2, y2 = group[i]
            abstand = math.hypot(x2 - x1, y2 - y1)
            if abstand > distance_threshold:
                new_groups.append(current_subgroup)
                current_subgroup = [group[i]]
            else:
                current_subgroup.append(group[i])
        if current_subgroup:
            new_groups.append(current_subgroup)
    return new_groups

def convert_groups_to_textfields(groups, img_width_px, img_height_px, min_points_per_line, dpi: int):
    textfields = []
    for group in groups:
        if len(group) < min_points_per_line:
            continue
        min_x = min(point[0] for point in group)
        max_x = max(point[0] for point in group)
        min_y = min(point[1] for point in group)
        max_y = max(point[1] for point in group)

        # Hinzufügen eines Textfeld-Objekts mit den Eckenkoordinaten
        textfields.append(Textfeld(
            links_oben=Punkt(x=min_x, y=min_y - mm_to_pixel(5, dpi)),
            rechts_unten=Punkt(x=max_x, y=max_y + mm_to_pixel(1, dpi))
        ))
    return textfields

def draw_textfields_on_image(image, textfields):
    for tf in textfields:
        cv2.rectangle(
            image,
            (tf.links_oben.x, tf.links_oben.y),
            (tf.rechts_unten.x, tf.rechts_unten.y),
            (0, 255, 0),  # Grün
            2
        )

def linien_punkte_erkennen(
    pil_image: Image.Image,
    distance_threshold: float = 20,
    tolerance_y: int = 5,
    min_points_per_line: int = 5,
    dpi: int = 300
) -> List[Textfeld]:
    """
    Erkennt gepunktete, isolierte horizontale Linien in einem Bild.

    Args:
        pil_image (Image.Image): Eingabebild als PIL Image.
        distance_threshold (float, optional): Maximaler Abstand zwischen zwei Punkten,
                                              um sie als zusammengehörig zu betrachten.
                                              Defaults to 20.
        tolerance_y (int, optional): Toleranz für die Gruppierung von Punkten nach Y-Koordinate.
                                     Defaults to 5.
        min_points_per_line (int, optional): Mindestanzahl von Punkten, die eine Linie haben muss,
                                             um als valide erkannt zu werden. Defaults to 5.

    Returns:
        List[Textfeld]: Liste der erkannten gepunkteten Linien als Textfeld-Objekte.
    """

    # Konvertiere PIL Image zu OpenCV BGR Format und in Graustufen
    img_array = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)

    # Erkenne kleine gefüllte Kreise (Punkte)
    points = detect_small_filled_circles(gray)
    if not points:
        print("Keine Punkte erkannt.")
        return []

    # Gruppiere Punkte nach Y-Koordinate
    grouped_points = group_points_by_y(points, tolerance=tolerance_y)

    # Teile Gruppen basierend auf dem X-Abstand
    split_groups = split_groups_by_x_distance(grouped_points, distance_threshold)

    # Konvertiere Gruppen in Textfeld-Objekte
    img_height_px, img_width_px = gray.shape[:2]
    textfields = convert_groups_to_textfields(split_groups, img_width_px, img_height_px, min_points_per_line, dpi)

    return textfields


class Trude:
    def __init__(self, pfad_zu_einstellungen_json: str):
        self.pfad_zu_einstellungen_json = pfad_zu_einstellungen_json

    def einstellungen(self) -> dict:
        with open(self.pfad_zu_einstellungen_json, 'r', encoding="latin") as file:
            data = json.load(file)
        return data

    def elemente_sortieren(self, elemente: List) -> List:
        """
        Sortiert die Elemente basierend auf ihrer Position (links oben),
        mit einer Toleranz von ±2 Pixel auf der y-Achse.

        Elemente mit ähnlichen y-Koordinaten werden anhand der x-Koordinaten sortiert.
        """

        def key_function(element):
            # Extrahiere die links_oben Koordinaten für die Sortierung
            return element.links_oben.y, element.links_oben.x

        # Sortiere zuerst nach y-Koordinate (mit Toleranz) und dann nach x-Koordinate
        elemente.sort(key=lambda elem: (round(elem.links_oben.y / 2) * 2, elem.links_oben.x))
        return elemente

    def convert_pdf(self, pfad_zu_pdf: str, speicherpfad: str, dpi: int = 300):
        s = self.einstellungen()
        pil_images = convert_from_path(pfad_zu_pdf, dpi=dpi)

        # Dateiname extrahieren
        dateiname = Path(pfad_zu_pdf).name  # Pfadobjekt verwenden, um den Dateinamen zu extrahieren

        # Endung entfernen
        dateiname_ohne_endung = Path(dateiname).stem

        f = Formular(dateiname_ohne_endung, dpi)

        for i, pil_image in enumerate(pil_images):

            elemente = []

            if s["linien"]["active"]:
                print("linien aktiv")
                elemente.extend(linien_erkennen(
                    pil_image,
                    dpi=dpi,
                    min_width=s["linien"]["min_width"],
                    dilation_kernel_size=(s["linien"]["dilation_kernel_size_x"], s["linien"]["dilation_kernel_size_y"])
                ))

            if s["linien_punkte"]["active"]:
                print("linien_punkte aktiv")
                elemente.extend(linien_punkte_erkennen(
                    pil_image,
                    dpi=dpi,
                    distance_threshold=s["linien_punkte"]["distance_threshold"],
                    tolerance_y=s["linien_punkte"]["tolerance_y"],
                    min_points_per_line=s["linien_punkte"]["min_points_per_line"]
                ))

            if s["kaestchen"]["active"]:
                print("kaestchen aktiv")
                elemente.extend(kaestchen_erkennen(
                    pil_image,
                    min_height=s["kaestchen"]["min_height"],
                    min_width=s["kaestchen"]["min_width"],
                    max_height=s["kaestchen"]["max_height"],
                    max_width=s["kaestchen"]["max_width"],
                    approx_epsilon_factor=s["kaestchen"]["approx_epsilon_factor"],
                    dilation_kernel_size=(s["kaestchen"]["dilation_kernel_size_x"], s["kaestchen"]["dilation_kernel_size_y"]),
                    center_tolerance=s["kaestchen"]["center_tolerance"]
                ))

            if s["kreise"]["active"]:
                print("kreise aktiv")
                elemente.extend(kreise_erkennen(
                    pil_image,
                    min_radius=s["kreise"]["min_radius"],
                    max_radius=s["kreise"]["max_radius"],
                    umgebung_puffer=s["kreise"]["umgebung_puffer"],
                    epsilon_formfaktor=s["kreise"]["epsilon_formfaktor"],
                    epsilon_aspektverhaeltnis=s["kreise"]["epsilon_aspektverhaeltnis"],
                    solidity_threshold=s["kreise"]["solidity_threshold"],
                    dilation_kernel_size=(s["kreise"]["dilation_kernel_size_x"], s["kreise"]["dilation_kernel_size_y"])
                ))

            if s["zellen"]["active"]:
                print("zellen aktiv")
                elemente.extend(zellen_erkennen(
                    pil_image,
                    min_height=s["zellen"]["min_height"],
                    min_width=s["zellen"]["min_width"],
                    max_height=s["zellen"]["max_height"],
                    max_width=s["zellen"]["max_width"],
                    approx_epsilon_factor=s["zellen"]["approx_epsilon_factor"],
                    dilation_kernel_size=(s["zellen"]["dilation_kernel_size_x"], s["zellen"]["dilation_kernel_size_y"]),
                    center_tolerance=s["zellen"]["center_tolerance"],
                    padding=s["zellen"]["padding"],
                    max_perc_white_pixels=s["zellen"]["max_perc_white_pixels"]
                ))

            f.new_page(self.elemente_sortieren(elemente), pil_image)

        # Endung ändern
        neuer_dateiname = Path(dateiname).with_suffix('.dict')

        # Basispfad als Pfadobjekt
        basispfad = Path(speicherpfad)

        # Zusammenfügen
        voller_pfad = basispfad / neuer_dateiname

        f.write(voller_pfad)

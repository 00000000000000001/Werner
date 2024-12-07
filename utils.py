def mm_to_pixel(mm: float, dpi: int) -> int:
    """
    Wandelt eine Länge in Millimetern in Pixel um basierend auf der DPI.

    Parameter
    ---------
    mm : float
        Länge in Millimetern.
    dpi : int
        DPI (dots per inch) des Bildes.

    Returns
    -------
    int
        Entsprechende Länge in Pixeln.
    """
    # Ein Zoll (inch) entspricht 25.4 mm
    inches = mm / 25.4  # Millimeter in Zoll umrechnen
    pixels = inches * dpi  # Zoll in Pixel umrechnen
    return int(round(pixels))

def pixel_to_inches(pixel: float, dpi: int) -> float:
        return pixel / dpi

def pixel_to_mm(pixel: float, dpi: int) -> float:
    """
    Wandelt eine Pixelanzahl in Millimeter um basierend auf der DPI des Bildes.

    Parameter
    ---------
    pixel : int
        Anzahl der Pixel.
    dpi : float
        DPI (dots per inch) des Bildes.

    Returns
    -------
    float
        Entsprechender Wert in Millimetern.
    """
    # Ein Zoll (inch) entspricht 25.4 mmn
    mm = pixel_to_inches(pixel, dpi) * 25.4    # Zoll in Millimeter umrechnen
    return mm

def pixel_to_points(pixel: float, dpi: int) -> float:
    """
    Wandelt eine Pixelanzahl in Points um basierend auf der DPI des Bildes.

    Parameter
    ---------
    pixel : float
        Anzahl der Pixel.
    dpi : int
        DPI (dots per inch) des Bildes.

    Returns
    -------
    float
        Entsprechender Wert in Points.
    """
    # Pixel -> Inches -> Points
    points = (pixel / dpi) * 72  # Unabhängig von 72 DPI, basiert auf der Relation Zoll -> Points
    return points

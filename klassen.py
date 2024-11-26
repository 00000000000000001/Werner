class Rechteck:
    def __init__(self, x1, y1, x2, y2, dpi=300):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.dpi = dpi

    def to_mm(self):
        """Konvertiert die Koordinaten von Pixel zu mm und gibt ein neues Rechteck-Objekt zurück"""
        pixel_pro_mm = self.dpi / 25.4
        return Rechteck(
            x1=self.x1 / pixel_pro_mm,
            y1=self.y1 / pixel_pro_mm,
            x2=self.x2 / pixel_pro_mm,
            y2=self.y2 / pixel_pro_mm,
            dpi=self.dpi
        )

    def __repr__(self):
        return (f"Rechteck(x1={self.x1:.2f}, y1={self.y1:.2f}, "
                f"x2={self.x2:.2f}, y2={self.y2:.2f}, "
                f"Breite={self.breite_mm():.2f} mm, Höhe={self.hoehe_mm():.2f} mm)")

    def __str__(self):
        return f"Rechteck von ({self.x1:.2f}, {self.y1:.2f}) mm bis ({self.x2:.2f}, {self.y2:.2f}) mm"

    def breite_mm(self):
        return abs(self.x2 - self.x1)

    def hoehe_mm(self):
        return abs(self.y2 - self.y1)


class Textfeld(Rechteck):
    def to_mm(self):
        """Konvertiert die Koordinaten von Pixel zu mm und gibt ein neues Textfeld-Objekt zurück"""
        pixel_pro_mm = self.dpi / 25.4
        return Textfeld(
            x1=self.x1 / pixel_pro_mm,
            y1=self.y1 / pixel_pro_mm,
            x2=self.x2 / pixel_pro_mm,
            y2=self.y2 / pixel_pro_mm,
            dpi=self.dpi
        )

class Ankreuzfeld(Rechteck):
    def to_mm(self):
        """Konvertiert die Koordinaten von Pixel zu mm und gibt ein neues Ankreuzfeld-Objekt zurück"""
        pixel_pro_mm = self.dpi / 25.4
        return Ankreuzfeld(
            x1=self.x1 / pixel_pro_mm,
            y1=self.y1 / pixel_pro_mm,
            x2=self.x2 / pixel_pro_mm,
            y2=self.y2 / pixel_pro_mm,
            dpi=self.dpi
        )

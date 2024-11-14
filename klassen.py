# Definiere die Klasse Textfeld
class Rechteck:
    def __init__(self, x1_mm, y1_mm, x2_mm, y2_mm):
        self.x1_mm = x1_mm
        self.y1_mm = y1_mm
        self.x2_mm = x2_mm
        self.y2_mm = y2_mm

class Textfeld(Rechteck):
    pass

class Ankreuzfeld(Rechteck):
    pass

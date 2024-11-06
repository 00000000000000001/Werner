class Feld:
    def __init__(self, x_in_mm, y_in_mm):
        self.x_in_mm = x_in_mm
        self.y_in_mm = y_in_mm

class Ankreuzfeld(Feld):
    pass

class Textfeld(Feld):
    def __init__(self, x_in_mm, y_in_mm, w_in_mm):
        super().__init__(x_in_mm, y_in_mm)
        self.w_in_mm = w_in_mm

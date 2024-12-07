import tkinter as tk

TOOLTIPS = {
    "min_height": "Moin! Dat is' die Mindesthöhe für so 'ne Zelle, verstehste? Wenn die Zelle zu klein is', schmeiß' die raus. Hau den Wert rauf, wenn zu viele Fliegenklatschen erkannt werden.",
    "min_width": "Hiermit sagst du, wie breit 'ne Zelle mindestens sein muss. Ziemlich schlau, wa? Wenn dir zu viele Zahnstocher angezeigt werden, mach den Wert größer.",
    "max_height": "Jo, und dat hier is' die maximale Höhe. Alles, was größer is' als 'n Heizkessel, fliegt raus. Mach den Wert kleiner, wenn nur noch Monsterzellen durchkommen.",
    "max_width": "Mit diesem Wert sortierste die breiten Dinger aus. Willste keine flachen Bretter? Dann setz 'nen kleinen Wert rein.",
    "approx_epsilon_factor": "Pass uff: Das hier bestimmt, wie genau wir die Konturen anpassen. Klein is' genau, aber langsamer. Groß is' mehr 'Jo, passt schon!'.",
    "dilation_kernel_size_x": "Dat is' die Breite vom Filter, der kleine Lücken zuschmiert. Mach den größer, wenn du dickere Verbindungen willst.",
    "dilation_kernel_size_y": "Und das is' die Höhe vom Filter. Hau hier 'nen größeren Wert rein, wenn du vertikal mehr schließen willst.",
    "center_tolerance": "Wenn Zellen doppelt erkannt werden, isses mit diesem Wert vorbei. Größerer Wert heißt: Du tolerierst mehr Klumpatsch in der Mitte.",
    "padding": "Jo, dat is' der Platz, den wir um 'ne erkannte Zelle drumrum machen. Brauchst du mehr Luft? Dann hau den Wert hoch!",
    "max_perc_white_pixels": "Hiermit bestimmste, wie viel Zeuch in 'ner Zelle sein darf. Zu viel Zeuch? Dann schraub den Wert runter und hol dir die leeren Dinger ran.",
    "distance_threshold": "So nah dürfen zwei Punkte beieinander sein, damit wir sagen: Dat gehört zusammen! Wenn du 'ne Party veranstalten willst, mach den Wert höher.",
    "tolerance_y": "Hier wird entschieden, wie weit Punkte auf der Y-Achse auseinander sein dürfen, bevor wir sie trennen. Viel Toleranz = dicke Freundschaft zwischen den Punkten!",
    "min_points_per_line": "Wenn 'ne Linie aus mindestens so vielen Punkten bestehen muss, dann isses 'ne richtige Linie. Weniger Punkte? Pff, dat is' nur Rumgekritzel.",
    "min_radius": "Nur Kreise mit mindestens diesem Radius kommen rein. Mach den Wert größer, wenn du die Mücken loswerden willst.",
    "max_radius": "Alles über diesem Radius is' raus! Kein Platz für XXL-Kreise, verstehste? Mach den Wert kleiner, wenn du nur handliche Größen haben willst.",
    "umgebung_puffer": "Gibt 'n kleinen Sicherheitsabstand um Kreise. Brauchst du mehr Platz für die dicken Dinger? Hau hier 'ne größere Zahl rein.",
    "epsilon_formfaktor": "Dat hier sagt, wie kreisförmig 'n Kreis sein muss. Klein bedeutet: Perfekter Kreis, genau wie 'ne Radkappe!",
    "epsilon_aspektverhaeltnis": "Wie rund darf der Kreis sein? Wert nahe null heißt: Kein Platz für Ovale. Willste Eier? Dann hau 'nen größeren Wert rein.",
    "solidity_threshold": "Bestimmt, wie solide 'n Objekt sein muss. Fast wie beim TÜV: Löcher und Flatterkram? Nix da, Wert hoch und nur feste Sachen reinlassen!",
    "active": "Willste diesen Erkennungstyp überhaupt benutzen? Aktivier ihn, wenn er dir passt, und sonst: Weg damit!",
    "dpi": "Die Auflösung von deinem Bild. Mehr Punkte pro Zoll, aber auch mehr Rechenpower. Dat macht ordentlich Dampf, wenn's hoch genug is'!",
}




class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        # Binde Mausereignisse
        widget.bind("<Enter>", self.show_tooltip)
        widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        if self.tooltip_window:
            return

        # Fenster für Tooltip erstellen
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 20
        y += self.widget.winfo_rooty() + 20

        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Entfernt Rahmen
        tw.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="white",
            relief="solid",
            borderwidth=1,
            font=("Comic Sans MS", 10)
        )
        label.pack(ipadx=5, ipady=5)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

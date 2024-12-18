import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from python_gedcom_2.parser import Parser
from python_gedcom_2.element.individual import IndividualElement
import tkinter.font as tkFont
from python_gedcom_2.element.element import Element

import csv


class MainWindow(tk.Tk):
    def __init__(self, parser: Parser, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser = parser
        self.current_frame: tk.Frame | None = None
        self.config(bg="#36312D")
        self.container = tk.Frame(self, bg="#36312D")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)
        self.show_frame(SelectorFrame)

    def show_frame(self, frame_class, *args, **kwargs) -> None:
        for widget in self.container.winfo_children():
            widget.destroy()
        frame = frame_class(self.container, self, *args, **kwargs)
        frame.grid(row=0, column=0, sticky="nsew")
        self.current_frame = frame
        frame.tkraise()


class SelectorFrame(tk.Frame):
    def __init__(self, parent: tk.Frame, controller: MainWindow):
        super().__init__(parent, bg="#36312D")
        self.controller = controller
        self.logo_image_original = Image.open("./images/logo.png")
        self.logo_label = tk.Label(self, bg="#36312D")
        self.logo_label.place(relx=0.5, rely=0.3, anchor="center")
        self.drop_area = tk.Frame(self, bg="#36312D")
        self.drop_area.place(relx=0.5, rely=0.7, anchor="center", relwidth=0.6, relheight=0.2)
        self.button_canvas = tk.Canvas(self.drop_area, highlightthickness=0, bg="#36312D")
        self.button_canvas.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.3, relheight=0.5)
        self.button_canvas.bind("<Configure>", self.resize_elements)
        self.button_canvas.bind("<Button-1>", self.on_button_click)
        self.after_idle(self.initial_draw)

    def initial_draw(self):
        self.update_idletasks()
        event = type('event', (object,), {'width': self.button_canvas.winfo_width(), 'height': self.button_canvas.winfo_height()})
        self.resize_elements(event)

    def choose_file(self):
        file_path = filedialog.askopenfilename(
            title="Wähle eine GEDCOM-Datei aus",
            filetypes=[("GEDCOM-Dateien", "*.ged"), ("Alle Dateien", "*.*")]
        )
        if file_path:
            try:
                self.controller.parser.parse_file(file_path)
                self.controller.show_frame(DisplayFrame)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Datei: {e}")

    def on_button_click(self, event):
        self.choose_file()

    def draw_rounded_rect_button(self, canvas_width, canvas_height):
        self.button_canvas.delete("all")
        border_color = "#A48164"
        bg_color = "#BF9874"
        text_color = "#ffffff"
        border_thickness = 4
        corner_radius = min(canvas_width, canvas_height) * 0.2
        x1, y1 = 0, 0
        x2, y2 = canvas_width, canvas_height
        ix1, iy1 = border_thickness, border_thickness
        ix2, iy2 = canvas_width - border_thickness, canvas_height - border_thickness
        self._draw_rounded_rect(self.button_canvas, x1, y1, x2, y2, corner_radius, border_color)
        self._draw_rounded_rect(self.button_canvas, ix1, iy1, ix2, iy2, corner_radius - border_thickness, bg_color)
        font_size = max(8, int(canvas_height * 0.3))
        self.button_canvas.create_text(
            canvas_width / 2,
            canvas_height / 2,
            text="Datei auswählen",
            fill=text_color,
            font=("Arial", font_size, "bold")
        )

    def _draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, color):
        canvas.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, fill=color, outline=color)
        canvas.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, fill=color, outline=color)
        canvas.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, fill=color, outline=color)
        canvas.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, fill=color, outline=color)
        canvas.create_rectangle(x1 + r, y1, x2 - r, y1 + r, fill=color, outline=color)
        canvas.create_rectangle(x1 + r, y2 - r, x2 - r, y2, fill=color, outline=color)
        canvas.create_rectangle(x1, y1 + r, x1 + r, y2 - r, fill=color, outline=color)
        canvas.create_rectangle(x2 - r, y1 + r, x2, y2 - r, fill=color, outline=color)
        canvas.create_rectangle(x1 + r, y1 + r, x2 - r, y2 - r, fill=color, outline=color)

    def resize_elements(self, event):
        width = self.winfo_width()
        if width > 0:
            logo_size = int(width * 0.2)
            if logo_size > 0:
                resized_logo = self.logo_image_original.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(resized_logo)
                self.logo_label.config(image=self.logo_photo)
        canvas_w = self.button_canvas.winfo_width()
        canvas_h = self.button_canvas.winfo_height()
        if canvas_w > 0 and canvas_h > 0:
            self.draw_rounded_rect_button(canvas_w, canvas_h)


class DisplayFrame(tk.Frame):
    def __init__(self, parent: tk.Frame, controller: MainWindow, start_person_name: str = None):
        super().__init__(parent, bg="#36312D")
        self.controller = controller
        self.start_person_name = start_person_name
        self.create_menu_bar()

        self.container = tk.Frame(self, bg="#36312D")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.container, bg="#36312D", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky='nsew')

        self.vbar = tk.Scrollbar(self.container, orient='vertical', command=self.canvas.yview)
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar = tk.Scrollbar(self.container, orient='horizontal', command=self.canvas.xview)
        self.hbar.grid(row=1, column=0, sticky='ew')
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)

        self.horizontal_gap = 30
        self.vertical_gap = 80
        self.vertical_padding = 10
        self.horizontal_padding = 20
        self.font = tkFont.Font(family="Arial", size=12, weight="normal")
        self.objects = {}

        elements = self.controller.parser.get_root_child_elements()
        eldest = [
            element for element in elements
            if isinstance(element, IndividualElement) and not element.is_child_in_a_family()
        ]
        start = [element for element in self.controller.parser.get_root_child_elements() if isinstance(element, IndividualElement) and element.get_name() == start_person_name]

        if start_person_name is not None and start is not None:
            self.draw_tree(start[0], 1000, 50)
        elif eldest:
            self.draw_tree(eldest[0], 1000, 50)
            self.start_person_name = eldest[0].get_name()

        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def create_menu_bar(self):
        """Erstellt eine horizontale Menüleiste mit einem Logo und Buttons, die unterschiedlich groß sind."""
        menu_bar = tk.Frame(self, bg="#2F2A25", height=70)
        menu_bar.pack(side="top", fill="x")

        menu_bar.grid_columnconfigure(0, weight=1)
        menu_bar.grid_columnconfigure(1, weight=1)
        menu_bar.grid_columnconfigure(2, weight=1)
        menu_bar.grid_columnconfigure(3, weight=2)

        logo_image = Image.open("images/logo.png").resize((60, 60), Image.Resampling.LANCZOS)
        self.logo_photo = ImageTk.PhotoImage(logo_image)
        logo_label = tk.Label(menu_bar, image=self.logo_photo, bg="#2F2A25")
        logo_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        button_config = [
            {"image_path": "images/Exportieren.png", "command": self.export_data, "size": (60, 60)},
            {"image_path": "images/Speichern.png", "command": self.save_data, "size": (60, 60)},
            #{"image_path": "images/Zoom in.png", "command": self.zoom_in, "size": (50, 50)},
            #{"image_path": "images/Zoom out.png", "command": self.zoom_out, "size": (50, 50)},
            {"image_path": "images/Lupe.png", "command": self.search_person, "size": (60, 47)},
        ]

        for i, config in enumerate(button_config):
            button_image = Image.open(config["image_path"]).resize(config["size"], Image.Resampling.LANCZOS)
            button_photo = ImageTk.PhotoImage(button_image)
            button = tk.Button(menu_bar, image=button_photo, bg="#2F2A25", bd=0, highlightthickness=0,
                               command=config["command"])
            button.image = button_photo
            button.grid(row=0, column=i+1, padx=10, pady=5, sticky="nsew")

    def on_menu_button_click(self, index):
        """Wird aufgerufen, wenn ein Button in der Menüleiste geklickt wird."""
        if index == 0:
            self.export_data()
        elif index == 1:
            self.save_data()
        elif index == 2:
            self.zoom_in()
        elif index == 3:
            self.zoom_out()
        elif index == 4:
            self.search_person()

    def export_data(self):
        """Exportiert die aktuellen Daten als CSV-Datei."""
        file_path = filedialog.asksaveasfilename(
            title="Exportiere die Daten",
            defaultextension=".csv",
            filetypes=[("CSV-Dateien", "*.csv"), ("Alle Dateien", "*.*")]
        )
        if file_path:
            try:
                invid = []
                for element in self.controller.parser.get_root_child_elements():
                    if isinstance(element,IndividualElement):
                        invid.append(element)

                data = []
                for i in invid:
                    if i.get_birth_element():
                        if i.get_birth_element().has_date():
                            birt = i.get_birth_element().get_date_element().get_value()
                        else:
                            birt = None
                    else:
                        birt = None
                    if i.get_death_element():
                        if i.get_death_element().has_date():
                            deat = i.get_death_element().get_date_element().get_value()
                        else:
                            deat = None
                    else:
                        deat = None
                    children = self.controller.parser.get_children(i)
                    child_names = ""
                    for child in children:
                        child_names += child.get_name() +"; "
                    child_names = child_names[:-2]
                    parents = self.controller.parser.get_parents(i)
                    parent_str = ""
                    for parent in parents:
                        if parent:
                            parent_str += parent.get_name() + "; "
                    parent_str = parent_str[:-2]
                    data.append([i.get_name(), i.get_gender(), i.get_occupation(), birt, deat, child_names, parent_str])

                data_dicts = [dict(zip(["Name", "Gender", "Arbeit", "Geburt", "Tod", "Kinder", "Eltern (V,M)"], row)) for row in data]
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    csvwriter = csv.DictWriter(
                        csvfile,
                        fieldnames=["Name", "Gender", "Arbeit", "Geburt", "Tod", "Kinder", "Eltern (V,M)"],
                        delimiter=',',
                        quotechar='"',
                        quoting=csv.QUOTE_MINIMAL
                    )
                    csvwriter.writeheader()

                    csvwriter.writerows(data_dicts)

                messagebox.showinfo("Exportieren", f"Datei erfolgreich exportiert nach {file_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Exportieren: {e}")

    def save_data(self):
        """Speichert die aktuellen Änderungen."""
        file_path = filedialog.asksaveasfilename(
            title="Speichern",
            defaultextension=".ged",
            filetypes=[("GEDCOM-Dateien", "*.ged"), ("Alle Dateien", "*.*")]
        )
        if file_path and file_path.endswith(".ged"):
            with open(file_path, "w+", encoding="utf-8") as file:
                self.controller.parser.save_gedcom(file)
                messagebox.showinfo("Speichern", "Daten wurden erfolgreich gespeichert.")

    def zoom_in(self):
        """Zoomt in die Ansicht hinein und passt die Schriftgröße an."""
        scale_factor = 1.2
        self.canvas.scale("all", 0, 0, scale_factor, scale_factor)
        self.update_font_size(scale_factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def zoom_out(self):
        """Zoomt aus der Ansicht heraus und passt die Schriftgröße an."""
        scale_factor = 0.8
        self.canvas.scale("all", 0, 0, scale_factor, scale_factor)
        self.update_font_size(scale_factor)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_font_size(self, scale_factor):
        """Passt die Schriftgröße basierend auf dem Zoom-Faktor an."""
        current_size = self.font['size']
        new_size = max(8, int(current_size * scale_factor))  # Mindestgröße der Schrift = 8
        self.font.configure(size=new_size)


    def search_person(self):
        """Öffnet ein Suchfenster, um nach Personen zu suchen."""
        SearchWindow(self, self.controller)

    def get_node_dimensions(self, person: IndividualElement):
        name = person.get_name()
        text_width = self.font.measure(name)
        node_width = text_width + self.horizontal_padding
        node_height = self.font.metrics("linespace") + self.vertical_padding
        return node_width, node_height

    def subtree_width(self, person: IndividualElement) -> int:
        children = self.controller.parser.get_children(person)
        node_width, _ = self.get_node_dimensions(person)
        if not children:
            return node_width
        children_widths = [self.subtree_width(child) for child in children]
        total_children_width = sum(children_widths) + self.horizontal_gap * (len(children) - 1)
        return max(node_width, total_children_width)

    def draw_tree(self, person: IndividualElement, x: int, y: int):
        node_width, node_height = self.get_node_dimensions(person)
        x1 = x - node_width / 2
        y1 = y
        x2 = x + node_width / 2
        y2 = y + node_height
        rect_id = self.canvas.create_rectangle(x1, y1, x2, y2, fill="#7D625B", outline="#E9E4E1")
        text_id = self.canvas.create_text(x, y + node_height / 2, text=person.get_name(), fill="#ffffff", font=self.font)
        self.objects[rect_id] = person.get_pointer()
        self.objects[text_id] = person.get_pointer()

        self.canvas.tag_bind(rect_id, "<Button-1>", lambda e, item_id=rect_id: self.object_click_event(e, item_id))
        self.canvas.tag_bind(text_id, "<Button-1>", lambda e, item_id=text_id: self.object_click_event(e, item_id))

        children = self.controller.parser.get_children(person)

        if not children:
            return

        children_widths = [self.subtree_width(child) for child in children]
        total_children_width = sum(children_widths) + self.horizontal_gap * (len(children) - 1)
        child_top_y = y + node_height + self.vertical_gap
        start_x = x - total_children_width / 2
        for i, child in enumerate(children):
            cw = children_widths[i]
            child_x = start_x + cw / 2
            child_y = child_top_y
            mid_y = (y2 + child_y) / 2
            self.canvas.create_line(x, y2, x, mid_y, fill="#A48164")
            self.canvas.create_line(x, mid_y, child_x, mid_y, fill="#A48164")
            self.canvas.create_line(child_x, mid_y, child_x, child_y, fill="#A48164")
            self.draw_tree(child, child_x, child_y)
            start_x += cw + self.horizontal_gap

    def object_click_event(self, event, item_id):
        if item_id in self.objects:
            pointer = self.objects[item_id]
            person = self.controller.parser.get_element_by_pointer(pointer)
            EditPopup(person, self.controller)


class SearchWindow:
    def __init__(self, parent, controller: MainWindow):
        self.parent = parent
        self.controller = controller
        self.parser = controller.parser

        self.window = tk.Toplevel(self.parent)
        self.window.title("Person suchen")
        self.window.geometry("300x200")
        self.window.config(bg="#2F2A25")

        self.search_label = tk.Label(self.window, text="Name der Person:", bg="#2F2A25", fg="white")
        self.search_label.pack(pady=5)

        self.search_entry = tk.Entry(self.window)
        self.search_entry.pack(pady=5)
        self.search_entry.bind("<KeyRelease>", self.update_suggestions)

        self.suggestion_list = tk.Listbox(self.window)
        self.suggestion_list.pack(pady=5, fill=tk.BOTH, expand=True)
        self.suggestion_list.bind("<<ListboxSelect>>", self.on_select)

    def update_suggestions(self, event):
        input_text = self.search_entry.get().lower()
        self.suggestion_list.delete(0, tk.END)

        if input_text:
            for element in self.parser.get_element_list():
                if isinstance(element, IndividualElement):
                    name = element.get_name().lower()
                    if input_text in name:
                        self.suggestion_list.insert(tk.END, element.get_name())

    def on_select(self, event):
        selected_index = self.suggestion_list.curselection()
        if selected_index:
            selected_name = self.suggestion_list.get(selected_index[0])
            self.controller.show_frame(DisplayFrame, start_person_name = selected_name)


class EditPopup(tk.Toplevel):
    def __init__(self, person: IndividualElement, controller: MainWindow):
        super().__init__()
        self.controller = controller
        self.person = person

        self.title("Daten ändern")
        self.configure(bg="#7A534D")

        self.entries: dict[Element, tk.Entry] = {}

        child_tags: list[Element] = person.get_child_elements().copy()
        i = 1
        while len(child_tags) > 0:
            element = child_tags.pop(0)
            if isinstance(element, Element):
                self.entries[element] = self.create_label_entry(element.get_value(), i, element.get_tag())
                for child in element.get_child_elements():
                    child_tags.insert(0, child)

            i += 1

        fertig_button = tk.Button(
            self,
            text="Fertig",
            bg="#D5A77C",
            fg="white",
            font=("Helvetica", 12, "bold"),
            relief="flat",
            command=self.on_fertig_click
        )
        fertig_button.grid(row=i, column=0, columnspan=2, pady=20)

        self.text = tk.Label(self, text=self.person.to_gedcom_string(True), anchor="w", justify="left")
        self.text.grid(row=0, column=2, rowspan=i, padx=20, pady=10, sticky="nsew")

    def create_label_entry(self, text, row, labeltext) -> tk.Entry:
        label = tk.Label(self, text=labeltext, bg="#7A534D", fg="white", font=("Helvetica", 12, "bold"))
        label.grid(row=row, column=0, padx=20, sticky="w")
        entry = tk.Entry(self, font=("Helvetica", 12), bg="#B38B82", fg="black", relief="flat")
        if not text:
            entry.config(state="disabled", bg="#57534F")
        entry.insert(0, text)
        entry.grid(row=row, column=1, padx=20)
        return entry

    def on_fertig_click(self):
        changed = False
        for element, entry in self.entries.items():
            if entry.get() != element.get_value():
                element.set_value(entry.get())
                changed = True

        if changed and isinstance(self.controller.current_frame, DisplayFrame):
            self.controller.show_frame(DisplayFrame, start_person_name=self.controller.current_frame.start_person_name)
        self.destroy()


if __name__ == "__main__":
    p: Parser = Parser()
    main = MainWindow(p)
    main.title("Roots Revealed - Ancestry Research")
    main.state("zoomed")
    main.mainloop()

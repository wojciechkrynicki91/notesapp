from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.utils import get_color_from_hex
from functools import partial
import json
import os
import random

NOTES_FILE = "notes.json"

KV = """
BoxLayout:
    orientation: "vertical"
    spacing: 10
    padding: 10
    canvas.before:
        Color:
            rgba: app.bg_color
        Rectangle:
            pos: self.pos
            size: self.size

    MDLabel:
        text: "Moje Notatki :)"
        halign: "center"
        theme_text_color: "Custom"
        text_color: 0,0,0,1
        font_style: "H4"
        size_hint_y: None
        height: 60

    MDTextField:
        id: note_title_input
        hint_text: "Tytuł notatki..."
        multiline: False
        size_hint_y: None
        height: 50

    MDTextField:
        id: note_content_input
        hint_text: "Treść notatki..."
        multiline: True
        size_hint_y: None
        height: 80

    MDRaisedButton:
        text: "Dodaj notatkę"
        size_hint_y: None
        height: 50
        on_release: app.add_note()

    ScrollView:
        do_scroll_x: False
        do_scroll_y: True

        GridLayout:
            id: notes_grid
            cols: 2
            spacing: 10
            padding: 5
            size_hint_y: None
            height: self.minimum_height
"""

PASTEL_COLORS = [
    get_color_from_hex("#FFCDD2"), get_color_from_hex("#F8BBD0"),
    get_color_from_hex("#E1BEE7"), get_color_from_hex("#D1C4E9"),
    get_color_from_hex("#C5CAE9"), get_color_from_hex("#BBDEFB"),
    get_color_from_hex("#B3E5FC"), get_color_from_hex("#B2EBF2"),
    get_color_from_hex("#B2DFDB"), get_color_from_hex("#C8E6C9"),
    get_color_from_hex("#DCEDC8"), get_color_from_hex("#FFF9C4"),
    get_color_from_hex("#FFECB3"), get_color_from_hex("#FFE0B2"),
]

class EditNoteContent(BoxLayout):
    """Dialog edycji notatki w formie kartki z przyciskami pod spodem"""
    def __init__(self, title_text, content_text, card_color, save_callback, delete_callback, cancel_callback, **kwargs):
        super().__init__(orientation="vertical", spacing=10, padding=10, **kwargs)

        # MDCard z treścią - większa, aby była bardziej wyraźna
        self.card = MDCard(
            padding=20,
            radius=[12,12,12,12],
            orientation="vertical",
            size_hint_y=None,
            md_bg_color=card_color,
            elevation=10
        )

        # Tytuł wyboldowany
        self.title_label = MDLabel(
            text=title_text if title_text else "(Brak tytułu)",
            bold=True,
            halign="center",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None
        )
        self.title_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', instance.texture_size[1]+10))

        # Treść
        self.content_input = MDTextField(
            text=content_text,
            multiline=True,
            size_hint_y=None,
            height=250
        )

        self.card.add_widget(self.title_label)
        self.card.add_widget(self.content_input)
        self.card.bind(minimum_height=lambda instance, value: setattr(instance, 'height', instance.minimum_height))
        self.add_widget(self.card)

        # MDCard dla przycisków
        self.buttons_card = MDCard(
            radius=[12,12,12,12],
            padding=10,
            orientation="horizontal",
            spacing=10,
            size_hint_y=None,
            height=50
        )

        self.btn_delete = MDRaisedButton(text="USUŃ", on_release=delete_callback)
        self.btn_cancel = MDRaisedButton(text="ANULUJ", on_release=cancel_callback)
        self.btn_save = MDRaisedButton(text="ZAPISZ", on_release=save_callback)

        # Równomierne rozmieszczenie przycisków
        self.buttons_card.add_widget(self.btn_delete)
        self.buttons_card.add_widget(self.btn_cancel)
        self.buttons_card.add_widget(self.btn_save)

        self.add_widget(self.buttons_card)

class NotesApp(MDApp):
    dialog = None

    def build(self):
        self.bg_color = get_color_from_hex("#FFF9C4")  # jasny żółty
        self.notes = self.load_notes()
        self.root = Builder.load_string(KV)
        self.refresh_notes_grid()
        return self.root

    def load_notes(self):
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for i, note in enumerate(data):
                    if isinstance(note, str):
                        data[i] = {"title": "", "content": note}
                return data
        return []

    def save_notes(self):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.notes, f, ensure_ascii=False, indent=2)

    def refresh_notes_grid(self):
        self.root.ids.notes_grid.clear_widgets()
        for idx, note in enumerate(self.notes):
            color = random.choice(PASTEL_COLORS)

            card = MDCard(
                size_hint=(1, None),
                padding=10,
                radius=[12,12,12,12],
                elevation=6,
                orientation="vertical",
                md_bg_color=color
            )

            # AnchorLayout wyśrodkowuje tytuł w pionie i poziomie
            anchor = AnchorLayout(anchor_x="center", anchor_y="center", size_hint_y=None)
            anchor.height = 50

            title_label = MDLabel(
                text=note["title"] if note["title"] else "(Brak tytułu)",
                halign="center",
                theme_text_color="Primary",
                bold=False
            )

            anchor.add_widget(title_label)
            card.add_widget(anchor)

            card.bind(on_touch_down=partial(self.on_card_click, idx, color))
            self.root.ids.notes_grid.add_widget(card)

    def on_card_click(self, idx, color, instance, touch):
        if instance.collide_point(*touch.pos):
            self.show_note_dialog(idx, color)
            return True
        return False

    def add_note(self):
        title = self.root.ids.note_title_input.text.strip()
        content = self.root.ids.note_content_input.text.strip()
        if title or content:
            self.notes.append({"title": title, "content": content})
            self.save_notes()
            self.root.ids.note_title_input.text = ""
            self.root.ids.note_content_input.text = ""
            self.refresh_notes_grid()

    def show_note_dialog(self, idx, card_color):
        note = self.notes[idx]

        def save_callback(instance):
            self.save_edit_dialog(idx)
        def delete_callback(instance):
            self.delete_note_dialog(idx)
        def cancel_callback(instance):
            self.close_dialog()

        self.dialog = MDDialog(
            type="custom",
            content_cls=EditNoteContent(
                note["title"],
                note["content"],
                card_color,
                save_callback,
                delete_callback,
                cancel_callback
            ),
            auto_dismiss=False
        )
        self.dialog.open()

    def close_dialog(self, *args):
        if self.dialog:
            self.dialog.dismiss()

    def save_edit_dialog(self, idx):
        edit_input = self.dialog.content_cls
        new_title = edit_input.title_label.text.strip()
        new_content = edit_input.content_input.text.strip()
        self.notes[idx] = {"title": new_title, "content": new_content}
        self.save_notes()
        self.refresh_notes_grid()
        self.dialog.dismiss()

    def delete_note_dialog(self, idx):
        self.notes.pop(idx)
        self.save_notes()
        self.refresh_notes_grid()
        self.dialog.dismiss()

if __name__ == "__main__":
    NotesApp().run()
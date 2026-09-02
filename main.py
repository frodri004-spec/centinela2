from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.drawerlayout import DrawerLayout
from kivy.uix.scrollview import ScrollView

KV = '''
ScreenManager:
    MainScreen:

<MainScreen>:
    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            size_hint_y: None
            height: '56dp'
            padding: '12dp'
            spacing: '8dp'
            canvas.before:
                Color:
                    rgb: (0.04, 0.08, 0.12)
                Rectangle:
                    pos: self.pos
                    size: self.size

            Button:
                text: '☰'
                size_hint_x: None
                width: '48dp'
                on_release: root.open_drawer()
                background_color: (0.13, 0.41, 0.55, 1)

            Label:
                text: 'Centinela'
                color: (1, 1, 1, 1)
                bold: True
                font_size: '20sp'

            Label:
                text: 'Activo'
                color: (0.39, 0.86, 0.55, 1)
                halign: 'right'
                valign: 'middle'
                size_hint_x: None
                width: '90dp'

        ScreenManager:
            id: screens
            Screen:
                name: 'inicio'
                BoxLayout:
                    orientation: 'vertical'
                    padding: '20dp'
                    spacing: '12dp'
                    Label:
                        text: 'Bienvenido a Centinela'
                        font_size: '24sp'
                        bold: True
                        color: (0.88, 0.96, 1, 1)
                    Label:
                        text: 'Sistema de geolocalización y seguridad para personas en riesgo.'
                        text_size: self.width, None
                        halign: 'center'
                        valign: 'middle'
                        color: (0.76, 0.84, 0.93, 1)

            Screen:
                name: 'usuario'
                BoxLayout:
                    orientation: 'vertical'
                    padding: '20dp'
                    spacing: '10dp'
                    Label:
                        text: 'Perfil del usuario'
                        font_size: '22sp'
                        bold: True
                    Label:
                        text: 'Nombre: María González\nEdad: 32 años\nMunicipio: Metepec'
                        text_size: self.width, None
                        color: (0.76, 0.84, 0.93, 1)

            Screen:
                name: 'estado'
                BoxLayout:
                    orientation: 'vertical'
                    padding: '20dp'
                    spacing: '10dp'
                    Label:
                        text: 'Estado del sistema'
                        font_size: '22sp'
                        bold: True
                    Label:
                        text: 'Monitoreo activo\nSe está revisando ubicación y signos vitales.'
                        text_size: self.width, None
                        color: (0.76, 0.84, 0.93, 1)

            Screen:
                name: 'mapa'
                BoxLayout:
                    orientation: 'vertical'
                    padding: '20dp'
                    spacing: '10dp'
                    Label:
                        text: 'Mapa'
                        font_size: '22sp'
                        bold: True
                    Label:
                        text: 'Aquí se mostrará la ubicación geolocalizada.'
                        text_size: self.width, None
                        color: (0.76, 0.84, 0.93, 1)

<DrawerContent>:
    canvas.before:
        Color:
            rgb: (0.07, 0.12, 0.18)
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: '12dp'
        spacing: '8dp'
        Label:
            text: 'Centinela'
            bold: True
            font_size: '22sp'
            size_hint_y: None
            height: '40dp'
            color: (1, 1, 1, 1)
        Button:
            text: 'Inicio'
            on_release: app.change_screen('inicio')
            background_color: (0.13, 0.41, 0.55, 1)
        Button:
            text: 'Usuario'
            on_release: app.change_screen('usuario')
            background_color: (0.13, 0.41, 0.55, 1)
        Button:
            text: 'Estado'
            on_release: app.change_screen('estado')
            background_color: (0.13, 0.41, 0.55, 1)
        Button:
            text: 'Mapa'
            on_release: app.change_screen('mapa')
            background_color: (0.13, 0.41, 0.55, 1)
'''

Builder.load_string(KV)


class DrawerContent(BoxLayout):
    pass


class MainScreen(Screen):
    drawer = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.drawer = DrawerLayout()
        self.drawer.size_hint = (1, 1)
        self.drawer.add_widget(self._build_content())
        self.add_widget(self.drawer)

    def _build_content(self):
        drawer_content = DrawerContent(size_hint_x=0.7)
        return drawer_content

    def open_drawer(self):
        self.drawer.open()


class CentinelaApp(App):
    def build(self):
        self.screen_manager = ScreenManager()
        self.main_screen = MainScreen(name='main')
        self.screen_manager.add_widget(self.main_screen)
        return self.screen_manager

    def change_screen(self, name):
        self.screen_manager.current = name
        if hasattr(self.main_screen, 'drawer'):
            self.main_screen.drawer.dismiss()


if __name__ == '__main__':
    CentinelaApp().run()

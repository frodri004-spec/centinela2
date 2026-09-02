import platform
import os
if platform.system() == 'Windows':
    os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

KV = '''
ScreenManager:
    LoginScreen:
    HomeScreen:
    UserScreen:
    StatusScreen:
    MapScreen:

<LoginScreen>:
    name: 'login'
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        canvas.before:
            Color:
                rgba: (0.03, 0.07, 0.12, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Centinela'
            bold: True
            font_size: '34sp'
            color: (0.91, 0.97, 1, 1)
            size_hint_y: 0.3

        Label:
            text: 'Seguridad inteligente para tu bienestar'
            font_size: '16sp'
            color: (0.72, 0.84, 0.94, 1)
            halign: 'center'
            text_size: self.width, None
            size_hint_y: 0.2

        Button:
            text: 'Ingresar'
            size_hint_y: None
            height: '52dp'
            background_color: (0.10, 0.67, 0.82, 1)
            background_normal: ''
            color: (1, 1, 1, 1)
            on_release: root.manager.current = 'home'

<HomeScreen>:
    name: 'home'
    BoxLayout:
        orientation: 'vertical'
        canvas.before:
            Color:
                rgba: (0.08, 0.12, 0.18, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        BoxLayout:
            size_hint_y: None
            height: '60dp'
            padding: ['12dp', '12dp']
            canvas.before:
                Color:
                    rgba: (0.05, 0.09, 0.15, 1)
                Rectangle:
                    pos: self.pos
                    size: self.size

            Label:
                text: '☰'
                font_size: '28sp'
                size_hint_x: None
                width: '50dp'
                color: (0.10, 0.67, 0.82, 1)

            Label:
                text: 'Centinela'
                bold: True
                color: (1, 1, 1, 1)
                font_size: '22sp'

            Label:
                text: 'Activo'
                halign: 'right'
                color: (0.42, 0.88, 0.60, 1)
                font_size: '14sp'
                size_hint_x: None
                width: '80dp'

        BoxLayout:
            orientation: 'vertical'
            padding: 18
            spacing: 12

            BoxLayout:
                orientation: 'vertical'
                padding: 18
                spacing: 8
                canvas.before:
                    Color:
                        rgba: (0.12, 0.18, 0.25, 1)
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [18]

                Label:
                    text: 'Panel principal'
                    bold: True
                    font_size: '20sp'
                    color: (0.95, 0.98, 1, 1)

                Label:
                    text: 'Monitoreo activo y protección en curso.'
                    color: (0.72, 0.84, 0.94, 1)
                    text_size: self.width, None
                    halign: 'center'

            BoxLayout:
                size_hint_y: None
                height: '110dp'
                spacing: 12

                BoxLayout:
                    orientation: 'vertical'
                    padding: 14
                    canvas.before:
                        Color:
                            rgba: (0.15, 0.27, 0.38, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [18]
                    Label:
                        text: 'Ubicación'
                        color: (0.72, 0.84, 0.94, 1)
                    Label:
                        text: '19.4326, -99.1332'
                        bold: True
                        color: (1, 1, 1, 1)

                BoxLayout:
                    orientation: 'vertical'
                    padding: 14
                    canvas.before:
                        Color:
                            rgba: (0.22, 0.48, 0.42, 1)
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [18]
                    Label:
                        text: 'Señales'
                        color: (0.85, 0.97, 0.90, 1)
                    Label:
                        text: 'FC 78 | SpO2 98%'
                        bold: True
                        color: (1, 1, 1, 1)

            Button:
                text: 'Botón de pánico'
                size_hint_y: None
                height: '50dp'
                background_color: (0.82, 0.19, 0.25, 1)
                background_normal: ''
                color: (1, 1, 1, 1)

            Button:
                text: 'Ver estado'
                size_hint_y: None
                height: '50dp'
                background_color: (0.10, 0.67, 0.82, 1)
                background_normal: ''
                color: (1, 1, 1, 1)
                on_release: root.manager.current = 'status'

<UserScreen>:
    name: 'user'
    BoxLayout:
        orientation: 'vertical'
        padding: 24
        spacing: 16
        canvas.before:
            Color:
                rgba: (0.08, 0.12, 0.18, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Perfil del usuario'
            bold: True
            font_size: '24sp'
            color: (0.95, 0.98, 1, 1)

        BoxLayout:
            orientation: 'vertical'
            padding: 18
            spacing: 8
            canvas.before:
                Color:
                    rgba: (0.12, 0.18, 0.25, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [18]

            Label:
                text: 'María González López'
                bold: True
                color: (1, 1, 1, 1)
            Label:
                text: 'Edad: 32 años\\nMunicipio: Metepec\\nGrupo sanguíneo: A+'
                color: (0.72, 0.84, 0.94, 1)
                text_size: self.width, None

        Button:
            text: 'Volver al inicio'
            size_hint_y: None
            height: '48dp'
            background_color: (0.10, 0.67, 0.82, 1)
            background_normal: ''
            on_release: root.manager.current = 'home'

<StatusScreen>:
    name: 'status'
    BoxLayout:
        orientation: 'vertical'
        padding: 24
        spacing: 16
        canvas.before:
            Color:
                rgba: (0.08, 0.12, 0.18, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Estado del sistema'
            bold: True
            font_size: '24sp'
            color: (0.95, 0.98, 1, 1)

        BoxLayout:
            orientation: 'vertical'
            padding: 18
            spacing: 8
            canvas.before:
                Color:
                    rgba: (0.12, 0.18, 0.25, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [18]

            Label:
                text: 'Monitoreo activo'
                bold: True
                color: (0.42, 0.88, 0.60, 1)
            Label:
                text: 'Frecuencia cardiaca: 78 lpm\\nSpO2: 98%\\nUbicación segura'
                color: (0.72, 0.84, 0.94, 1)
                text_size: self.width, None

        Button:
            text: 'Volver'
            size_hint_y: None
            height: '48dp'
            background_color: (0.10, 0.67, 0.82, 1)
            background_normal: ''
            on_release: root.manager.current = 'home'

<MapScreen>:
    name: 'map'
    BoxLayout:
        orientation: 'vertical'
        padding: 24
        spacing: 16
        canvas.before:
            Color:
                rgba: (0.08, 0.12, 0.18, 1)
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Mapa'
            bold: True
            font_size: '24sp'
            color: (0.95, 0.98, 1, 1)

        BoxLayout:
            orientation: 'vertical'
            padding: 18
            spacing: 8
            canvas.before:
                Color:
                    rgba: (0.12, 0.18, 0.25, 1)
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [18]

            Label:
                text: 'Coordenadas: 19.4326, -99.1332'
                color: (0.72, 0.84, 0.94, 1)
            Label:
                text: 'Zona: Ciudad de México'
                color: (0.72, 0.84, 0.94, 1)

        Button:
            text: 'Volver'
            size_hint_y: None
            height: '48dp'
            background_color: (0.10, 0.67, 0.82, 1)
            background_normal: ''
            on_release: root.manager.current = 'home'
'''

Builder.load_string(KV)

class LoginScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

class UserScreen(Screen):
    pass

class StatusScreen(Screen):
    pass

class MapScreen(Screen):
    pass

class CentinelaKivyApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(UserScreen(name='user'))
        sm.add_widget(StatusScreen(name='status'))
        sm.add_widget(MapScreen(name='map'))
        sm.current = 'login'
        return sm

if __name__ == '__main__':
    CentinelaKivyApp().run()
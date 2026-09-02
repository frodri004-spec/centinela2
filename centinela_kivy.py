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
                rgba: (0.15, 0.35, 0.55, 1)  # Azul más claro
            Rectangle:
                pos: self.pos
                size: self.size

        Label:
            text: 'Centinela'
            bold: True
            font_size: '40sp'
            color: (1, 1, 1, 1)
            size_hint_y: 0.4
            halign: 'center'
            valign: 'middle'

        Label:
            text: 'Seguridad inteligente para tu bienestar'
            font_size: '18sp'
            color: (0.9, 0.95, 1, 1)
            halign: 'center'
            text_size: self.width, None
            size_hint_y: 0.3

        Button:
            text: 'INGRESAR'
            size_hint_y: None
            height: '60dp'
            background_color: (0.20, 0.80, 0.90, 1)  # Cian brillante
            background_normal: ''
            color: (1, 1, 1, 1)
            font_size: '20sp'
            bold: True
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
        # Configurar tamaño de ventana
        from kivy.core.window import Window
        Window.size = (400, 700)
        Window.clearcolor = (0.15, 0.35, 0.55, 1)  # Fondo azul
        
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
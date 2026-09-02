# menu_hamburguesa.py
import tkinter as tk

class MenuHamburguesa:
    """Componente de menú hamburguesa reutilizable para Tkinter"""
    
    def __init__(self, parent, colores=None):
        self.parent = parent
        self.menu_abierto = False
        self.animacion_activa = False
        self.ancho_actual = 0
        self.ancho_destino = 180
        
        # Colores por defecto
        self.colores = colores or {
            'bg': '#050816',
            'sidebar': '#0b1229',
            'text': '#e0f2fe',
            'accent': '#22d3ee',
            'hover': '#1a3a5c'
        }
        
        self._build_menu()
    
    def _build_menu(self):
        """Construye el menú hamburguesa"""
        # Frame contenedor principal
        self.container = tk.Frame(self.parent, bg=self.colores['bg'])
        self.container.pack(fill="both", expand=True)
        
        # Header con botón hamburguesa
        self.header = tk.Frame(self.container, bg=self.colores['bg'], height=62)
        self.header.pack(fill="x", padx=12, pady=(12, 8))
        self.header.pack_propagate(False)
        
        # Botón hamburguesa
        self.menu_btn = tk.Button(
            self.header,
            text="☰",
            font=("Segoe UI", 24),
            bg=self.colores['bg'],
            fg=self.colores['text'],
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self.toggle_menu
        )
        self.menu_btn.pack(side="left", padx=(0, 10))
        
        # Título (puede ser actualizado desde fuera)
        self.titulo_label = tk.Label(
            self.header,
            text="Centinela",
            font=("Segoe UI", 20, "bold"),
            bg=self.colores['bg'],
            fg=self.colores['text']
        )
        self.titulo_label.pack(side="left")
        
        # Estado del sistema
        self.status_label = tk.Label(
            self.header,
            text="● Detenido",
            font=("Segoe UI", 10),
            bg=self.colores['bg'],
            fg="#dc2626"
        )
        self.status_label.pack(side="right")
        
        # --- Sidebar (menú deslizable) ---
        self.sidebar = tk.Frame(
            self.container,
            bg=self.colores['sidebar'],
            width=0,
            height=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.sidebar.config(width=0)
        
        # --- Contenido principal ---
        self.content_frame = tk.Frame(
            self.container,
            bg=self.colores['bg']
        )
        self.content_frame.pack(side="right", fill="both", expand=True)
        
        # --- Frame para botones del menú ---
        self.menu_frame = tk.Frame(self.sidebar, bg=self.colores['sidebar'])
        self.menu_frame.pack(fill="both", expand=True, padx=10, pady=18)
        
        # Variable para guardar referencias a los botones
        self.menu_items = []
        self.item_callbacks = {}
    
    def agregar_item(self, texto, callback, icono="•"):
        """Agrega un item al menú"""
        btn = tk.Button(
            self.menu_frame,
            text=f"{icono} {texto}",
            font=("Segoe UI", 13),
            bg=self.colores['sidebar'],
            fg=self.colores['text'],
            relief="flat",
            bd=0,
            anchor="w",
            padx=18,
            pady=10,
            cursor="hand2",
            command=callback
        )
        btn.pack(fill="x", pady=4)
        self.menu_items.append(btn)
        
        # Efecto hover
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.colores['hover']))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.colores['sidebar']))
        
        return btn
    
    def agregar_separador(self):
        """Agrega un separador en el menú"""
        sep = tk.Frame(self.menu_frame, bg=self.colores['sidebar'], height=2)
        sep.pack(fill="x", pady=10)
        return sep
    
    def toggle_menu(self):
        """Abre o cierra el menú"""
        if self.animacion_activa:
            return
        
        self.menu_abierto = not self.menu_abierto
        self.animacion_activa = True
        
        if self.menu_abierto:
            self.ancho_destino = 180
            self.menu_btn.config(text="✕")
        else:
            self.ancho_destino = 0
            self.menu_btn.config(text="☰")
        
        self._animar_menu()
    
    def _animar_menu(self):
        """Animación del menú"""
        paso = 16
        if self.menu_abierto:
            if self.ancho_actual < self.ancho_destino:
                self.ancho_actual = min(self.ancho_actual + paso, self.ancho_destino)
                self.sidebar.config(width=self.ancho_actual)
                self.parent.after(12, self._animar_menu)
            else:
                self.animacion_activa = False
        else:
            if self.ancho_actual > self.ancho_destino:
                self.ancho_actual = max(self.ancho_actual - paso, self.ancho_destino)
                self.sidebar.config(width=self.ancho_actual)
                self.parent.after(12, self._animar_menu)
            else:
                self.animacion_activa = False
    
    def cerrar_menu(self):
        """Cierra el menú si está abierto"""
        if self.menu_abierto:
            self.toggle_menu()
    
    def set_titulo(self, texto):
        """Actualiza el título del header"""
        self.titulo_label.config(text=texto)
    
    def set_estado(self, texto, color="#10b981"):
        """Actualiza el estado del sistema"""
        self.status_label.config(text=texto, fg=color)
    
    def get_content_frame(self):
        """Devuelve el frame donde se mostrará el contenido"""
        return self.content_frame
    
    def limpiar_contenido(self):
        """Limpia el contenido actual"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
            widget.destroy()
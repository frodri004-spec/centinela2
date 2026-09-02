"""
╔══════════════════════════════════════════════════════════════════════════════╗
║           CENTINELA - Sistema de Geolocalización y Seguridad               ║
║         Monitoreo mediante Arete/Pulsera IoT — México                      ║
║                                                                              ║
║  Funcionalidades:                                                            ║
║  • Geolocalización en tiempo real                                           ║
║  • Monitoreo de signos vitales (FC, SpO2, temperatura corporal)             ║
║  • Evaluación de riesgo por zona en México                                  ║
║  • Alertas automáticas a autoridades (911, SSPC)                            ║
║  • Notificaciones a familiares vía SMS y email                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random
import time
import json
import smtplib
import logging
import threading
import math
import os
import tempfile
from datetime import datetime, timedelta
from menu_hamburguesa import MenuHamburguesa
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from enum import Enum
from queue import Queue, Empty
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import webbrowser
try:
    import winsound
except ImportError:
    winsound = None

try:
    import cv2  # type: ignore[import]
except ImportError:
    cv2 = None

try:
    from PIL import Image, ImageTk  # type: ignore[import]
except ImportError:
    Image = None
    ImageTk = None

try:
    import tkintermapview
except ImportError:
    tkintermapview = None

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL SISTEMA
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ENUMERACIONES
# ─────────────────────────────────────────────────────────────────────────────

class NivelRiesgo(Enum):
    BAJO    = ("BAJO",    "🟢", "#27ae60")
    MEDIO   = ("MEDIO",   "🟡", "#f39c12")
    ALTO    = ("ALTO",    "🟠", "#e67e22")
    CRITICO = ("CRÍTICO", "🔴", "#e74c3c")

    def __init__(self, label, emoji, color):
        self.label = label
        self.emoji = emoji
        self.color = color


class EstadoSignosVitales(Enum):
    NORMAL   = "NORMAL"
    ALERTA   = "ALERTA"
    CRITICO  = "CRÍTICO"
    SIN_DATO = "SIN_DATO"


# ─────────────────────────────────────────────────────────────────────────────
# ZONAS DE RIESGO EN MÉXICO
# Basado en índices de seguridad y estadísticas del SNSP
# ─────────────────────────────────────────────────────────────────────────────

ZONAS_MEXICO = {
    # (lat_min, lat_max, lon_min, lon_max): info de zona
    "Ciudad de México Centro": {
        "coords": (19.40, 19.46, -99.17, -99.10),
        "riesgo": NivelRiesgo.MEDIO,
        "descripcion": "Zona turística y comercial, vigilancia moderada",
        "autoridad_local": "SSC CDMX",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Evitar mostrar objetos de valor",
            "Usar transporte formal",
            "Permanecer en zonas iluminadas"
        ]
    },
    "Tepito / Guerrero CDMX": {
        "coords": (19.44, 19.47, -99.14, -99.11),
        "riesgo": NivelRiesgo.ALTO,
        "descripcion": "Zona de alta incidencia delictiva en CDMX",
        "autoridad_local": "SSC CDMX / FGJCDMX",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Evitar la zona en horario nocturno",
            "No caminar solo",
            "Tener contacto frecuente con familiares"
        ]
    },
    "Guadalajara Centro": {
        "coords": (20.66, 20.70, -103.36, -103.32),
        "riesgo": NivelRiesgo.MEDIO,
        "descripcion": "Centro histórico de Guadalajara",
        "autoridad_local": "SSPH Jalisco",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Precaución en horarios nocturnos",
            "Vigilar pertenencias en mercados"
        ]
    },
    "Monterrey Centro": {
        "coords": (25.66, 25.70, -100.34, -100.30),
        "riesgo": NivelRiesgo.BAJO,
        "descripcion": "Zona metropolitana con buena seguridad",
        "autoridad_local": "Secretaría de Seguridad NL",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Zona generalmente segura",
            "Mantener precauciones estándar"
        ]
    },
    "Culiacán Sinaloa": {
        "coords": (24.78, 24.84, -107.40, -107.36),
        "riesgo": NivelRiesgo.CRITICO,
        "descripcion": "Alta presencia de crimen organizado",
        "autoridad_local": "SSPE Sinaloa / Guardia Nacional",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "EVITAR circulación nocturna",
            "Mantenerse en zonas conocidas",
            "Alertar a familiares de itinerario",
            "Contacto permanente con autoridades"
        ]
    },
    "Cancún Zona Hotelera": {
        "coords": (21.12, 21.18, -86.82, -86.76),
        "riesgo": NivelRiesgo.BAJO,
        "descripcion": "Zona turística con alta vigilancia",
        "autoridad_local": "SSP Quintana Roo",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Zona turística, buena vigilancia",
            "Precaución al salir de zona hotelera"
        ]
    },
    "Acapulco Centro": {
        "coords": (16.84, 16.88, -99.92, -99.88),
        "riesgo": NivelRiesgo.CRITICO,
        "descripcion": "Ciudad con alta tasa de criminalidad",
        "autoridad_local": "SSP Guerrero / Guardia Nacional",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "EVITAR zonas no turísticas",
            "Nunca circulen solos",
            "Permanecer en hoteles con seguridad",
            "Notificar ubicación constantemente"
        ]
    },
    "Metepec / Toluca": {
        "coords": (19.24, 19.28, -99.67, -99.63),
        "riesgo": NivelRiesgo.BAJO,
        "descripcion": "Zona suburbana con buena seguridad en Metepec",
        "autoridad_local": "SSC Estado de México",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Zona tranquila y bien comunicada",
            "Mantener alerta en cruces y avenidas principales"
        ]
    },
    "Mérida Centro": {
        "coords": (20.96, 21.02, -89.64, -89.60),
        "riesgo": NivelRiesgo.BAJO,
        "descripcion": "Una de las ciudades más seguras de México",
        "autoridad_local": "SSP Yucatán",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Ciudad considerada muy segura",
            "Precauciones estándar suficientes"
        ]
    },
    "Zona Desconocida": {
        "coords": (0, 90, -120, -85),
        "riesgo": NivelRiesgo.MEDIO,
        "descripcion": "Zona sin clasificación específica",
        "autoridad_local": "Guardia Nacional",
        "telefono_emergencia": "911",
        "recomendaciones": [
            "Verificar condiciones de seguridad locales",
            "Mantenerse comunicado"
        ]
    }
}


# ─────────────────────────────────────────────────────────────────────────────
# MODELOS DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Ubicacion:
    latitud: float
    longitud: float
    calle: str = ""
    altitud: float = 0.0
    precision_metros: float = 5.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    velocidad_kmh: float = 0.0
    direccion_grados: float = 0.0

    def distancia_a(self, otra: 'Ubicacion') -> float:
        """Calcula distancia en metros usando fórmula de Haversine"""
        R = 6371000
        lat1, lon1 = math.radians(self.latitud), math.radians(self.longitud)
        lat2, lon2 = math.radians(otra.latitud), math.radians(otra.longitud)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))

    def __str__(self):
        return f"{self.latitud:.6f}°N, {self.longitud:.6f}°W"


@dataclass
class SignosVitales:
    frecuencia_cardiaca: int          # lpm
    saturacion_oxigeno: float         # SpO2 %
    temperatura_corporal: float       # °C
    frecuencia_respiratoria: int      # resp/min
    presion_sistolica: int            # mmHg
    presion_diastolica: int           # mmHg
    nivel_actividad: str              # reposo / caminando / corriendo
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def estado(self) -> EstadoSignosVitales:
        """Evalúa el estado general de los signos vitales"""
        criticos = [
            self.frecuencia_cardiaca < 40 or self.frecuencia_cardiaca > 150,
            self.saturacion_oxigeno < 90,
            self.temperatura_corporal < 35.0 or self.temperatura_corporal > 40.0,
            self.presion_sistolica > 180 or self.presion_sistolica < 80,
        ]
        alertas = [
            self.frecuencia_cardiaca < 50 or self.frecuencia_cardiaca > 120,
            self.saturacion_oxigeno < 95,
            self.temperatura_corporal < 36.0 or self.temperatura_corporal > 38.5,
            self.presion_sistolica > 160 or self.presion_sistolica < 90,
        ]
        if any(criticos):
            return EstadoSignosVitales.CRITICO
        if any(alertas):
            return EstadoSignosVitales.ALERTA
        return EstadoSignosVitales.NORMAL

    def resumen(self) -> str:
        return (
            f"FC:{self.frecuencia_cardiaca}lpm | "
            f"SpO2:{self.saturacion_oxigeno:.1f}% | "
            f"Temp:{self.temperatura_corporal:.1f}°C | "
            f"PA:{self.presion_sistolica}/{self.presion_diastolica}mmHg"
        )


@dataclass
class Familiar:
    nombre: str
    telefono: str        # formato +521XXXXXXXXXX
    email: str
    relacion: str        # madre, padre, esposo, etc.
    prioridad: int = 1   # 1=primario, 2=secundario


@dataclass
class PerfilUsuario:
    nombre: str
    edad: int
    curp: str
    dispositivo_id: str
    tipo_dispositivo: str  # "arete" | "pulsera"
    municipio: str = "Metepec"
    estado: str = "Estado de México"
    calle: str = ""
    colonia: str = ""
    cp: str = ""
    numero: str = ""
    familiares: list[Familiar] = field(default_factory=list)
    condiciones_medicas: list[str] = field(default_factory=list)
    grupo_sanguineo: str = "O+"
    medicamentos: list[str] = field(default_factory=list)
    foto_url: str = ""


# ─────────────────────────────────────────────────────────────────────────────
# SENSOR SIMULADO (IoT)
# En producción: reemplazar con SDK del fabricante del wearable
# ─────────────────────────────────────────────────────────────────────────────

class SensorWearable:
    """
    Simula los sensores del arete/pulsera IoT.
    En producción conectar con BLE/WiFi al dispositivo real.
    """

    def __init__(self, dispositivo_id: str, tipo: str = "arete"):
        self.dispositivo_id = dispositivo_id
        self.tipo = tipo
        self._lat_origin = 19.256928
        self._lon_origin = -99.653165
        self._lat_base = self._lat_origin
        self._lon_base = self._lon_origin
        self._fc_base = 72
        self._bateria = 100.0
        self._conectado = True
        self._route_segments = [
            {"calle": "Av. Estado de México", "pasos": 12, "dlat": 0.00018, "dlon": 0.00003},
            {"calle": "Av. Tecnológico", "pasos": 10, "dlat": 0.00004, "dlon": -0.00020},
            {"calle": "Calle La Paz", "pasos": 10, "dlat": -0.00016, "dlon": -0.00002},
            {"calle": "Av. Las Torres", "pasos": 11, "dlat": -0.00002, "dlon": 0.00019},
            {"calle": "Calle Benito Juárez", "pasos": 10, "dlat": 0.00015, "dlon": 0.00004},
            {"calle": "Av. Lerdo", "pasos": 10, "dlat": -0.00010, "dlon": -0.00015},
            {"calle": "Calle Independencia", "pasos": 10, "dlat": 0.00008, "dlon": 0.00016},
            {"calle": "Av. Hidalgo", "pasos": 8, "dlat": -0.00018, "dlon": -0.00003}
        ]
        self._current_segment_index = 0
        self._current_step = 0
        self._street_name = self._route_segments[0]["calle"]
        log.info(f"[SENSOR] {tipo.upper()} {dispositivo_id} inicializado en Metepec")

    def leer_ubicacion(self) -> Ubicacion:
        """Lee GPS del dispositivo con variación realista y simula caminar calle por calle en Metepec"""
        if self._current_step >= self._route_segments[self._current_segment_index]["pasos"]:
            self._current_segment_index = (self._current_segment_index + 1) % len(self._route_segments)
            self._current_step = 0
            self._street_name = self._route_segments[self._current_segment_index]["calle"]

        segmento = self._route_segments[self._current_segment_index]
        paso_lat = segmento["dlat"]
        paso_lon = segmento["dlon"]
        self._lat_base += paso_lat
        self._lon_base += paso_lon
        self._current_step += 1

        # Mantener el recorrido dentro de un radio aproximado de 2 km alrededor de Metepec
        self._lat_base = min(max(self._lat_base, self._lat_origin - 0.018), self._lat_origin + 0.018)
        self._lon_base = min(max(self._lon_base, self._lon_origin - 0.022), self._lon_origin + 0.022)

        variacion_lat = random.gauss(0, 0.00003)
        variacion_lon = random.gauss(0, 0.00003)
        direccion = math.degrees(math.atan2(paso_lon, paso_lat)) if paso_lat or paso_lon else random.uniform(0, 360)

        return Ubicacion(
            latitud=self._lat_base + variacion_lat,
            longitud=self._lon_base + variacion_lon,
            calle=self._street_name,
            altitud=random.uniform(2200, 2250),
            precision_metros=random.uniform(3, 6),
            velocidad_kmh=random.uniform(3.5, 5.0),
            direccion_grados=(direccion + random.uniform(-10, 10)) % 360
        )

    def leer_signos_vitales(self) -> SignosVitales:
        """Lee todos los biosensores del dispositivo"""
        fc = int(random.gauss(self._fc_base, 8))
        return SignosVitales(
            frecuencia_cardiaca=max(35, min(200, fc)),
            saturacion_oxigeno=round(random.gauss(98.0, 0.8), 1),
            temperatura_corporal=round(random.gauss(36.8, 0.3), 1),
            frecuencia_respiratoria=int(random.gauss(16, 2)),
            presion_sistolica=int(random.gauss(120, 10)),
            presion_diastolica=int(random.gauss(80, 8)),
            nivel_actividad=random.choice(["reposo", "caminando", "caminando", "sentado"])
        )

    def simular_emergencia(self, tipo: str = "caida"):
        """Simula diferentes escenarios de emergencia para pruebas"""
        if tipo == "caida":
            self._fc_base = 110
            log.warning("[SENSOR] ⚠ Simulando caída detectada")
        elif tipo == "zona_peligrosa":
            self._lat_base = 16.86    # Acapulco
            self._lon_base = -99.90
            log.warning("[SENSOR] ⚠ Simulando entrada a zona peligrosa")
        elif tipo == "panico":
            self._fc_base = 145
            log.warning("[SENSOR] ⚠ Botón de pánico activado")

    @property
    def bateria(self) -> float:
        self._bateria = max(0, self._bateria - 0.01)
        return round(self._bateria, 1)

    @property
    def conectado(self) -> bool:
        return self._conectado


# ─────────────────────────────────────────────────────────────────────────────
# EVALUADOR DE RIESGO
# ─────────────────────────────────────────────────────────────────────────────

class EvaluadorRiesgo:
    """Determina el nivel de riesgo combinando zona geográfica y signos vitales"""

    def __init__(self):
        self.zonas = ZONAS_MEXICO

    def identificar_zona(self, ubicacion: Ubicacion) -> tuple[str, dict]:
        """Identifica en qué zona de riesgo se encuentra el usuario"""
        lat, lon = ubicacion.latitud, ubicacion.longitud
        for nombre_zona, datos in self.zonas.items():
            lmin, lmax, omin, omax = datos["coords"]
            if lmin <= lat <= lmax and omin <= lon <= omax:
                return nombre_zona, datos
        return "Zona Desconocida", self.zonas["Zona Desconocida"]

    def evaluar_riesgo_combinado(
        self,
        ubicacion: Ubicacion,
        signos: SignosVitales
    ) -> dict:
        """
        Combina riesgo geográfico + estado fisiológico
        para generar nivel de riesgo global
        """
        nombre_zona, datos_zona = self.identificar_zona(ubicacion)
        riesgo_zona = datos_zona["riesgo"]
        estado_sv = signos.estado

        # Escalado combinado
        nivel_zona = list(NivelRiesgo).index(riesgo_zona)
        nivel_sv = {
            EstadoSignosVitales.NORMAL: 0,
            EstadoSignosVitales.ALERTA: 1,
            EstadoSignosVitales.CRITICO: 3,
            EstadoSignosVitales.SIN_DATO: 1,
        }[estado_sv]

        nivel_total = min(3, nivel_zona + nivel_sv)
        riesgo_final = list(NivelRiesgo)[nivel_total]

        alertas = []
        if riesgo_zona == NivelRiesgo.CRITICO:
            alertas.append("⚠️  ZONA DE ALTO RIESGO DETECTADA")
        if riesgo_zona == NivelRiesgo.ALTO:
            alertas.append("🔶 Zona con alta incidencia delictiva")
        if estado_sv == EstadoSignosVitales.CRITICO:
            alertas.append("🚨 SIGNOS VITALES EN ESTADO CRÍTICO")
        if estado_sv == EstadoSignosVitales.ALERTA:
            alertas.append("⚡ Signos vitales fuera de rango normal")
        if signos.frecuencia_cardiaca > 130:
            alertas.append("💓 Taquicardia severa detectada")
        if signos.saturacion_oxigeno < 92:
            alertas.append("🫁 Saturación de oxígeno peligrosamente baja")
        if signos.temperatura_corporal > 39.5:
            alertas.append("🌡️ Fiebre alta detectada")

        return {
            "riesgo_final": riesgo_final,
            "riesgo_zona": riesgo_zona,
            "estado_signos": estado_sv,
            "nombre_zona": nombre_zona,
            "datos_zona": datos_zona,
            "alertas": alertas,
            "requiere_accion": riesgo_final in [NivelRiesgo.ALTO, NivelRiesgo.CRITICO]
                               or estado_sv == EstadoSignosVitales.CRITICO,
            "requiere_emergencia": riesgo_final == NivelRiesgo.CRITICO
                                    or estado_sv == EstadoSignosVitales.CRITICO,
        }


# ─────────────────────────────────────────────────────────────────────────────
# SISTEMA DE NOTIFICACIONES
# ─────────────────────────────────────────────────────────────────────────────

class GestorNotificaciones:
    """
    Gestiona el envío de alertas por múltiples canales.
    En producción: integrar Twilio, Firebase, API SSPC, etc.
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.historial_alertas: list[dict] = []
        self._ultima_alerta: dict[str, datetime] = {}
        self.cooldown_minutos = self.config.get("cooldown_alerta_minutos", 5)
        self.output_callback: Optional[Callable[[str], None]] = self.config.get("output_callback")

    def _imprimir(self, texto: str):
        if self.output_callback:
            self.output_callback(texto)
        else:
            log.info(texto)

    def _puede_enviar(self, clave: str) -> bool:
        """Evita spam de notificaciones repetidas"""
        if clave not in self._ultima_alerta:
            return True
        transcurrido = datetime.now() - self._ultima_alerta[clave]
        return transcurrido.total_seconds() > (self.cooldown_minutos * 60)

    def _registrar_alerta(self, tipo: str, destinatario: str, mensaje: str, exito: bool):
        entrada = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "destinatario": destinatario,
            "mensaje": mensaje[:200],
            "exito": exito
        }
        self.historial_alertas.append(entrada)
        self._ultima_alerta[f"{tipo}:{destinatario}"] = datetime.now()

    def enviar_sms_familiar(self, familiar: Familiar, mensaje: str) -> bool:
        """
        Envía SMS al familiar.
        En producción: usar Twilio SDK
          client = Client(TWILIO_SID, TWILIO_TOKEN)
          client.messages.create(to=familiar.telefono, from_="+1XXX", body=mensaje)
        """
        clave = f"sms:{familiar.telefono}"
        if not self._puede_enviar(clave):
            return False

        texto = (
            f"\n{'='*60}\n"
            f"📱 SMS → {familiar.nombre} ({familiar.telefono})\n"
            f"   Relación: {familiar.relacion}\n"
            f"   Mensaje: {mensaje}\n"
            f"{'='*60}"
        )
        self._imprimir(texto)
        self._registrar_alerta("SMS", familiar.telefono, mensaje, True)
        log.info(f"[SMS] Enviado a {familiar.nombre} — {familiar.telefono}")
        return True

    def enviar_email_familiar(self, familiar: Familiar, asunto: str, cuerpo: str) -> bool:
        """
        Envía email al familiar.
        En producción: configurar SMTP con credenciales reales en .env
        """
        clave = f"email:{familiar.email}"
        if not self._puede_enviar(clave):
            return False

        texto = (
            f"\n{'='*60}\n"
            f"📧 EMAIL → {familiar.nombre} <{familiar.email}>\n"
            f"   Asunto: {asunto}\n"
            f"   Cuerpo: {cuerpo[:300]}...\n"
            f"{'='*60}"
        )
        self._imprimir(texto)
        self._registrar_alerta("EMAIL", familiar.email, asunto, True)
        log.info(f"[EMAIL] Enviado a {familiar.nombre} — {familiar.email}")
        return True

    def notificar_autoridades(self, ubicacion: Ubicacion, usuario: PerfilUsuario,
                               evaluacion: dict) -> bool:
        """
        Alerta a autoridades competentes.
        En producción: usar API de C5 CDMX, SSPC, o sistema 911
        """
        zona = evaluacion["nombre_zona"]
        autoridad = evaluacion["datos_zona"]["autoridad_local"]
        tel = evaluacion["datos_zona"]["telefono_emergencia"]

        reporte = {
            "timestamp": datetime.now().isoformat(),
            "tipo_reporte": "ALERTA_WEARABLE",
            "usuario": {
                "nombre": usuario.nombre,
                "curp": usuario.curp,
                "edad": usuario.edad,
                "grupo_sanguineo": usuario.grupo_sanguineo,
                "medicamentos": usuario.medicamentos,
            },
            "ubicacion": {
                "latitud": ubicacion.latitud,
                "longitud": ubicacion.longitud,
                "precision_m": ubicacion.precision_metros,
                "link_maps": f"https://maps.google.com/?q={ubicacion.latitud},{ubicacion.longitud}"
            },
            "nivel_riesgo": evaluacion["riesgo_final"].label,
            "zona": zona,
            "alertas": evaluacion["alertas"],
        }

        texto = (
            f"\n{'🚨'*30}\n"
            f"  ALERTA ENVIADA A AUTORIDADES\n"
            f"  Autoridad: {autoridad}\n"
            f"  Teléfono: {tel}\n"
            f"  Reporte JSON:\n"
            f"{json.dumps(reporte, indent=4, ensure_ascii=False)}\n"
            f"{'🚨'*30}\n"
        )
        self._imprimir(texto)

        log.critical(f"[AUTORIDADES] Alerta enviada — {autoridad} | {zona}")
        return True

    def alertar_todos(self, usuario: PerfilUsuario, ubicacion: Ubicacion,
                       signos: SignosVitales, evaluacion: dict):
        """Orquesta el envío de alertas a todos los contactos"""
        riesgo = evaluacion["riesgo_final"]
        zona = evaluacion["nombre_zona"]
        alertas_txt = "\n".join(evaluacion["alertas"]) or "Situación monitoreada"
        maps_url = f"https://maps.google.com/?q={ubicacion.latitud},{ubicacion.longitud}"

        # Mensajes base
        sms_critico = (
            f"🚨 ALERTA CENTINELA\n"
            f"USUARIO: {usuario.nombre}\n"
            f"RIESGO: {riesgo.emoji} {riesgo.label}\n"
            f"ZONA: {zona}\n"
            f"VITALES: {signos.resumen()}\n"
            f"UBICACIÓN: {maps_url}\n"
            f"HORA: {datetime.now().strftime('%H:%M:%S')}"
        )

        sms_alerta = (
            f"⚠️ Centinela — {usuario.nombre}\n"
            f"Riesgo {riesgo.label} en {zona}\n"
            f"Ver ubicación: {maps_url}"
        )

        email_asunto = f"[Centinela] Alerta {riesgo.label} — {usuario.nombre}"
        email_cuerpo = f"""Centinela — Sistema de Protección Personal
{'═' * 50}

USUARIO: {usuario.nombre}
CURP: {usuario.curp}
EDAD: {usuario.edad} años
GRUPO SANGUÍNEO: {usuario.grupo_sanguineo}

NIVEL DE RIESGO: {riesgo.emoji} {riesgo.label}
ZONA: {zona}

SIGNOS VITALES:
    • Frecuencia Cardíaca: {signos.frecuencia_cardiaca} lpm
    • Saturación O₂: {signos.saturacion_oxigeno}%
    • Temperatura: {signos.temperatura_corporal}°C
    • Presión Arterial: {signos.presion_sistolica}/{signos.presion_diastolica} mmHg
    • Actividad: {signos.nivel_actividad}

ALERTAS DETECTADAS:
{alertas_txt}

UBICACIÓN GPS:
    Coordenadas: {ubicacion}
    Precisión: ±{ubicacion.precision_metros:.0f} m
    Ver en mapa: {maps_url}

RECOMENDACIONES:
{chr(10).join('  • ' + r for r in evaluacion['datos_zona']['recomendaciones'])}

Autoridad local: {evaluacion['datos_zona']['autoridad_local']}
Emergencias: {evaluacion['datos_zona']['telefono_emergencia']}

{'═' * 50}
Este mensaje fue generado automáticamente por Centinela.
Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        # Notificar familiares según prioridad y nivel de riesgo
        familiares_notificados = 0
        for familiar in sorted(usuario.familiares, key=lambda f: f.prioridad):
            if riesgo in [NivelRiesgo.CRITICO, NivelRiesgo.ALTO]:
                self.enviar_sms_familiar(familiar, sms_critico)
                self.enviar_email_familiar(familiar, email_asunto, email_cuerpo)
                familiares_notificados += 1
            elif riesgo == NivelRiesgo.MEDIO and familiar.prioridad == 1:
                self.enviar_sms_familiar(familiar, sms_alerta)
                familiares_notificados += 1

        # Notificar autoridades si es necesario
        if evaluacion["requiere_emergencia"]:
            self.notificar_autoridades(ubicacion, usuario, evaluacion)

        log.info(f"[NOTIF] {familiares_notificados} familiares notificados")
        return familiares_notificados


# ─────────────────────────────────────────────────────────────────────────────
# SISTEMA PRINCIPAL CENTINELA
# ─────────────────────────────────────────────────────────────────────────────

class GuardianWear:
    """
    Sistema central de monitoreo y protección personal.
    Integra sensor, evaluación de riesgo y notificaciones.
    """

    def __init__(self, usuario: PerfilUsuario, config: dict = None):
        self.usuario = usuario
        self.config = config or {}
        self.sensor = SensorWearable(usuario.dispositivo_id, usuario.tipo_dispositivo)
        self.evaluador = EvaluadorRiesgo()
        self.notificaciones = GestorNotificaciones(config)

        self.historial: list[dict] = []
        self.activo = False
        self._hilo_monitoreo: Optional[threading.Thread] = None
        self.output_callback: Optional[Callable[[str], None]] = self.config.get("output_callback")
        self.event_callback: Optional[Callable[[dict], None]] = self.config.get("event_callback")

        intervalo = self.config.get("intervalo_segundos", 30)
        log.info(f"[GUARDIAN] Sistema iniciado para {usuario.nombre}")
        log.info(f"[GUARDIAN] Dispositivo: {usuario.tipo_dispositivo.upper()} — {usuario.dispositivo_id}")
        log.info(f"[GUARDIAN] Intervalo de monitoreo: {intervalo}s")

    def ciclo_monitoreo(self) -> dict:
        """Ejecuta un ciclo completo de monitoreo"""
        ts = datetime.now()

        # 1. Leer sensores
        ubicacion = self.sensor.leer_ubicacion()
        signos = self.sensor.leer_signos_vitales()
        bateria = self.sensor.bateria

        # 2. Evaluar riesgo
        evaluacion = self.evaluador.evaluar_riesgo_combinado(ubicacion, signos)
        riesgo = evaluacion["riesgo_final"]

        # 3. Registrar en historial
        entrada = {
            "timestamp": ts.isoformat(),
            "ubicacion": asdict(ubicacion),
            "signos_vitales": asdict(signos),
            "evaluacion": {
                "riesgo": riesgo.label,
                "zona": evaluacion["nombre_zona"],
                "estado_sv": evaluacion["estado_signos"].value,
                "alertas": evaluacion["alertas"],
            },
            "bateria": bateria,
        }
        self.historial.append(entrada)
        if len(self.historial) > 1000:
            self.historial.pop(0)

        # 4. Registrar estado de ciclo mediante callback
        estado_texto = evaluacion["estado_signos"].value.lower()
        detalle = (
            f"[{ts.strftime('%H:%M:%S')}] "
            f"{riesgo.emoji} Todo está {riesgo.label.lower()}. "
            f"Zona detectada: {evaluacion['nombre_zona']}. "
            f"Pulso: {signos.frecuencia_cardiaca} latidos por minuto, "
            f"oxígeno: {signos.saturacion_oxigeno:.1f}%, "
            f"temperatura: {signos.temperatura_corporal:.1f}°C. "
            f"Batería: {bateria:.0f}%. "
            f"Estado general: {estado_texto}."
        )
        if self.output_callback:
            self.output_callback(detalle)
            if evaluacion["alertas"]:
                for alerta in evaluacion["alertas"]:
                    texto_alerta = alerta
                    if "ZONA DE ALTO RIESGO DETECTADA" in alerta:
                        texto_alerta = "⚠️ Estás entrando a una zona con mucho riesgo."
                    elif "Zona con alta incidencia delictiva" in alerta:
                        texto_alerta = "⚠️ La zona donde estás tiene una incidencia alta de delitos."
                    elif "SIGNOS VITALES EN ESTADO CRÍTICO" in alerta:
                        texto_alerta = "🚨 Los signos vitales están muy descontrolados."
                    elif "Signos vitales fuera de rango normal" in alerta:
                        texto_alerta = "⚡ Los signos vitales están fuera del rango normal."
                    elif "Taquicardia severa detectada" in alerta:
                        texto_alerta = "💓 Se detectó una frecuencia cardíaca muy alta."
                    elif "Saturación de oxígeno peligrosamente baja" in alerta:
                        texto_alerta = "🫁 La saturación de oxígeno está muy baja."
                    elif "Fiebre alta detectada" in alerta:
                        texto_alerta = "🌡️ Se detectó una temperatura corporal elevada."
                    self.output_callback(f"      {texto_alerta}")

        if self.event_callback:
            self.event_callback({
                "timestamp": ts.isoformat(),
                "riesgo": riesgo.label,
                "riesgo_emoji": riesgo.emoji,
                "zona": evaluacion["nombre_zona"],
                "alertas": evaluacion["alertas"],
                "estado_signos": evaluacion["estado_signos"].value,
                "bateria": bateria,
                "ubicacion": asdict(ubicacion),
                "signos_vitales": asdict(signos),
                "evaluacion": {
                    "riesgo": riesgo.label,
                    "zona": evaluacion["nombre_zona"],
                    "estado_sv": evaluacion["estado_signos"].value,
                    "alertas": evaluacion["alertas"],
                }
            })

        # 5. Enviar notificaciones si es necesario
        if evaluacion["requiere_accion"]:
            self.notificaciones.alertar_todos(
                self.usuario, ubicacion, signos, evaluacion
            )

        return entrada

    def _bucle_monitoreo(self):
        """Hilo de monitoreo continuo"""
        intervalo = self.config.get("intervalo_segundos", 30)
        while self.activo:
            try:
                self.ciclo_monitoreo()
                time.sleep(intervalo)
            except Exception as e:
                log.error(f"[GUARDIAN] Error en ciclo: {e}")
                time.sleep(5)

    def iniciar(self):
        """Inicia el monitoreo en segundo plano"""
        self.activo = True
        self._hilo_monitoreo = threading.Thread(
            target=self._bucle_monitoreo,
            daemon=True,
            name="Centinela-Monitor"
        )
        self._hilo_monitoreo.start()
        log.info("[GUARDIAN] ✅ Monitoreo iniciado")

    def detener(self):
        """Detiene el monitoreo"""
        self.activo = False
        if self._hilo_monitoreo:
            self._hilo_monitoreo.join(timeout=5)
        log.info("[GUARDIAN] ⏹ Monitoreo detenido")

    def activar_panico(self):
        """Activa alerta de pánico manual"""
        log.critical("[GUARDIAN] 🆘 BOTÓN DE PÁNICO ACTIVADO")
        self.sensor.simular_emergencia("panico")
        ubicacion = self.sensor.leer_ubicacion()
        signos = self.sensor.leer_signos_vitales()
        evaluacion = self.evaluador.evaluar_riesgo_combinado(ubicacion, signos)
        evaluacion["riesgo_final"] = NivelRiesgo.CRITICO
        evaluacion["alertas"].insert(0, "🆘 BOTÓN DE PÁNICO ACTIVADO POR EL USUARIO")
        evaluacion["requiere_emergencia"] = True
        self.notificaciones.alertar_todos(self.usuario, ubicacion, signos, evaluacion)

    def reporte_estado(self) -> str:
        """Genera reporte del estado actual del sistema"""
        if not self.historial:
            return "Sin datos aún"
        ultima = self.historial[-1]
        return json.dumps(ultima, indent=2, ensure_ascii=False)

    def exportar_historial(self, ruta: str = None):
        """Exporta el historial completo a JSON"""
        if ruta is None:
            # Carpeta de Documentos del usuario en cualquier SO
            docs = os.path.join(os.path.expanduser("~"), "Documents")
            os.makedirs(docs, exist_ok=True)
            ruta = os.path.join(docs, "historial_centinela.json")
        # Crear carpetas intermedias si no existen
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump({
                "usuario": self.usuario.nombre,
                "dispositivo": self.usuario.dispositivo_id,
                "exportado": datetime.now().isoformat(),
                "total_registros": len(self.historial),
                "historial": self.historial
            }, f, indent=2, ensure_ascii=False)
        log.info(f"[GUARDIAN] Historial exportado → {ruta}")
        return ruta


# ─────────────────────────────────────────────────────────────────────────────
# DEMOSTRACIÓN DEL SISTEMA
# ─────────────────────────────────────────────────────────────────────────────

def demo():
    print("\n" + "═" * 70)
    print("   CENTINELA — Sistema de Geolocalización y Protección Personal")
    print("   Versión 1.0 | México")
    print("═" * 70)

    # Configurar usuario de prueba
    usuario = PerfilUsuario(
        nombre="María González López",
        edad=32,
        curp="GOLM920315MDFNRR04",
        dispositivo_id="GW-ARETE-001",
        tipo_dispositivo="arete",
        grupo_sanguineo="A+",
        condiciones_medicas=["Hipertensión leve"],
        medicamentos=["Losartán 50mg"],
        familiares=[
            Familiar(
                nombre="Carlos González",
                telefono="+5215512345678",
                email="carlos.gonzalez@example.com",
                relacion="esposo",
                prioridad=1
            ),
            Familiar(
                nombre="Rosa López",
                telefono="+5215598765432",
                email="rosa.lopez@example.com",
                relacion="madre",
                prioridad=2
            ),
        ]
    )

    config = {
        "intervalo_segundos": 10,
        "cooldown_alerta_minutos": 2,
    }

    # Crear sistema
    guardian = GuardianWear(usuario, config)

    print(f"\n👤 Usuario: {usuario.nombre}")
    print(f"📟 Dispositivo: {usuario.tipo_dispositivo.upper()} — {usuario.dispositivo_id}")
    print(f"🩸 Grupo sanguíneo: {usuario.grupo_sanguineo}")
    print(f"👨‍👩‍👧 Familiares registrados: {len(usuario.familiares)}")

    # Demostración de 3 ciclos de monitoreo
    print("\n" + "─" * 70)
    print("  INICIANDO MONITOREO — Ciclo 1: Estado normal")
    print("─" * 70)
    guardian.ciclo_monitoreo()

    print("\n" + "─" * 70)
    print("  CICLO 2: Simulando entrada a zona peligrosa (Acapulco)")
    print("─" * 70)
    guardian.sensor.simular_emergencia("zona_peligrosa")
    guardian.ciclo_monitoreo()

    print("\n" + "─" * 70)
    print("  CICLO 3: Botón de pánico")
    print("─" * 70)
    guardian.sensor._lat_base = 19.4326  # Regresar a CDMX
    guardian.sensor._lon_base = -99.1332
    guardian.activar_panico()

    # Exportar historial
    # Exportar historial (se guarda en Documentos automáticamente)
    ruta = guardian.exportar_historial()
    print(f"\n✅ Historial exportado: {ruta}")
    print("\n═" * 35)
    print("  FIN DE DEMOSTRACIÓN CENTINELA")
    print("═" * 35 + "\n")

    return guardian


class InterfazGuardianWear:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Centinela — Centinela Mobile")
        self.root.minsize(400, 720)
        self.root.geometry("420x760")
        self.root.resizable(False, True)
        self.root.configure(bg="#08111f")

        self.queue = Queue()
        self.event_history = []
        self.event_popup = None
        self.registro_popup = None
        self.usuario = self._crear_usuario_demo()
        self.guardian = GuardianWear(self.usuario, {
            "intervalo_segundos": 3,
            "cooldown_alerta_minutos": 2,
            "output_callback": self._enqueue_log,
            "event_callback": self._enqueue_event,
        })

        self.menu = MenuHamburguesa(self.root, colores={
            'bg': '#08111f',
            'sidebar': '#0f172a',
            'text': '#e0f2fe',
            'accent': '#22d3ee',
            'hover': '#1e3a5f'
        })
        self.menu.set_titulo("Centinela")
        self.menu.set_estado("Sistema detenido", "#94a3b8")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._salir)
        self.root.after(200, self._procesar_cola)

    def _crear_usuario_demo(self) -> PerfilUsuario:
        return PerfilUsuario(
            nombre="María González López",
            edad=32,
            curp="GOLM920315MDFNRR04",
            dispositivo_id="GW-ARETE-001",
            tipo_dispositivo="arete",
            municipio="Metepec",
            estado="Estado de México",
            calle="Av. Estado de México",
            colonia="La Asunción",
            cp="52140",
            numero="123",
            grupo_sanguineo="A+",
            condiciones_medicas=["Hipertensión leve", "Diabetes tipo 2", "Convulsiones controladas"],
            medicamentos=["Losartán 50mg", "Metformina 500mg"],
            familiares=[
                Familiar(
                    nombre="Carlos González",
                    telefono="+5215512345678",
                    email="carlos.gonzalez@example.com",
                    relacion="esposo",
                    prioridad=1
                ),
                Familiar(
                    nombre="Rosa López",
                    telefono="+5215598765432",
                    email="rosa.lopez@example.com",
                    relacion="madre",
                    prioridad=2
                ),
            ]
        )

    def _build_ui(self):
        title_font = ("Segoe UI", 18, "bold")
        body_font = ("Segoe UI", 11)
        small_font = ("Segoe UI", 10)
        label_font = ("Segoe UI", 11, "bold")
        button_font = ("Segoe UI", 10, "bold")

        app_bg = "#3a4555"
        panel_bg = "#2a3050"
        panel_border = "#7fc3e8"
        text_color = "#e0f2fe"
        muted_text = "#a8d9f0"
        primary = "#6dd5e8"
        primary_hover = "#5bc3d9"
        info_bg = "#2d3e5f"
        stat_bg = "#3d4f6f"
        strong_bg = "#6eb8e8"

        button_style = {
            "font": button_font,
            "bg": primary,
            "fg": "#03111f",
            "activebackground": primary_hover,
            "activeforeground": "#03111f",
            "relief": "raised",
            "bd": 3,
            "highlightthickness": 2,
            "cursor": "hand2",
        }

        self.status_var = tk.StringVar(value="Sistema detenido")
        content_frame = self.menu.get_content_frame()
        content_frame.configure(bg=app_bg)

        self.pages = {}
        page_buttons = [
            ("Inicio", "inicio", "🏠"),
            ("Usuario", "usuario", "👤"),
            ("Controles", "controles", "⚙️"),
            ("Medico", "medico", "🩺"),
            ("Estado", "estado", "📊"),
            ("Mapa", "mapa", "📍"),
            ("Eventos", "eventos", "🧾"),
        ]

        for text, key, icon in page_buttons:
            self.menu.agregar_item(
                text,
                lambda k=key: (self._show_page(k), self.menu.cerrar_menu()),
                icono=icon
            )

        page_container = tk.Frame(content_frame, bg=app_bg)
        page_container.pack(fill="both", expand=True)
        page_container.grid_rowconfigure(0, weight=1)
        page_container.grid_columnconfigure(0, weight=1)

        def create_page(name):
            page = tk.Frame(page_container, bg=app_bg)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[name] = page
            return page

        inicio_page = create_page("inicio")
        usuario_page = create_page("usuario")
        controles_page = create_page("controles")
        medico_page = create_page("medico")
        estado_page = create_page("estado")
        mapa_page = create_page("mapa")
        eventos_page = create_page("eventos")

        tk.Label(inicio_page, text="Bienvenido a Centinela", font=title_font, bg=app_bg, fg=text_color).pack(pady=(24, 8))
        tk.Label(inicio_page, text="Utiliza las pestañas para ver cada pantalla: inicio, datos del usuario, controles, estado actual y mapa.", font=body_font, bg=app_bg, fg=muted_text, wraplength=360, justify="center").pack(padx=16)
        tk.Button(inicio_page, text="Registrar usuario", command=self._abrir_registro_usuario, **button_style).pack(pady=(18, 8), ipadx=10, ipady=6)

        info_frame = tk.Frame(usuario_page, bg=panel_bg, highlightbackground=panel_border, highlightthickness=1)
        info_frame.pack(fill="x", padx=0, pady=8)
        info_frame.grid_columnconfigure(1, weight=1)

        photo_frame = tk.Frame(info_frame, bg=panel_bg)
        photo_frame.grid(row=0, column=0, padx=12, pady=12, sticky="nw")
        self.user_photo_canvas = tk.Canvas(photo_frame, width=100, height=100, bg="#15263b", highlightthickness=0)
        self.user_photo_canvas.create_text(50, 50, text="Foto", fill=text_color, font=("Segoe UI", 10, "bold"))
        self.user_photo_canvas.pack()
        self.user_photo_label = tk.Label(photo_frame, text="Sin foto", font=("Segoe UI", 9), bg=panel_bg, fg=muted_text)
        self.user_photo_label.pack(pady=(8, 0))

        details_frame = tk.Frame(info_frame, bg=panel_bg)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(0,12), pady=12)

        self.user_name_label = tk.Label(details_frame, text=f"Nombre: {self.usuario.nombre}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_name_label.grid(row=0, column=0, sticky="w")
        self.user_age_label = tk.Label(details_frame, text=f"Edad: {self.usuario.edad} años", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_age_label.grid(row=1, column=0, sticky="w", pady=(6,0))
        self.user_curp_label = tk.Label(details_frame, text=f"CURP: {self.usuario.curp}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_curp_label.grid(row=2, column=0, sticky="w", pady=(6,0))
        self.user_device_label = tk.Label(details_frame, text=f"Dispositivo: {self.usuario.tipo_dispositivo.upper()} — {self.usuario.dispositivo_id}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_device_label.grid(row=3, column=0, sticky="w", pady=(6,0))
        self.user_blood_label = tk.Label(details_frame, text=f"Grupo sanguíneo: {self.usuario.grupo_sanguineo}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_blood_label.grid(row=4, column=0, sticky="w", pady=(6,0))

        address_frame = tk.LabelFrame(usuario_page, text="Domicilio", padx=12, pady=12, font=label_font, bg=panel_bg, fg=text_color, bd=1, relief="flat", highlightbackground=panel_border)
        address_frame.pack(fill="x", padx=0, pady=8)
        self.user_address1_label = tk.Label(address_frame, text=f"Calle: {self.usuario.calle} #{self.usuario.numero}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_address1_label.pack(fill="x", pady=(0,4))
        self.user_address2_label = tk.Label(address_frame, text=f"Colonia: {self.usuario.colonia}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_address2_label.pack(fill="x", pady=(0,4))
        self.user_address3_label = tk.Label(address_frame, text=f"Municipio: {self.usuario.municipio}, {self.usuario.estado}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_address3_label.pack(fill="x", pady=(0,4))
        self.user_address4_label = tk.Label(address_frame, text=f"C.P.: {self.usuario.cp}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_address4_label.pack(fill="x")

        clinic_frame = tk.LabelFrame(usuario_page, text="Historial clínico", padx=12, pady=12, font=label_font, bg=panel_bg, fg=text_color, bd=1, relief="flat", highlightbackground=panel_border)
        clinic_frame.pack(fill="x", padx=0, pady=8)
        condiciones = self.usuario.condiciones_medicas or ["Sin enfermedades registradas"]
        self.user_conditions = []
        for condicion in condiciones:
            label = tk.Label(clinic_frame, text=f"• {condicion}", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
            label.pack(fill="x", pady=(0,2))
            self.user_conditions.append(label)

        tk.Label(clinic_frame, text="Medicamentos:", anchor="w", font=label_font, bg=panel_bg, fg=text_color).pack(fill="x", pady=(8,0))
        self.user_medications_label = tk.Label(clinic_frame, text=", ".join(self.usuario.medicamentos) if self.usuario.medicamentos else "Ninguno", anchor="w", font=body_font, bg=panel_bg, fg=text_color)
        self.user_medications_label.pack(fill="x", pady=(2,0))

        self.pdf_path_var = tk.StringVar(value="Ningún PDF cargado.")
        self.pdf_loaded_path = None

        self.riesgo_var = tk.StringVar(value="N/A")
        self.calle_var = tk.StringVar(value="Calle inicial: Av. Estado de México")
        self.zona_var = tk.StringVar(value="N/A")
        self.bateria_var = tk.StringVar(value="N/A")
        self.estado_var = tk.StringVar(value="N/A")
        self.ultima_var = tk.StringVar(value="Sin datos aún")
        self.alerta_var = tk.StringVar(value="Sistema estable")

        controls_frame = tk.LabelFrame(controles_page, text="Controles", padx=12, pady=12, font=label_font, bg=panel_bg, fg=text_color, bd=1, relief="flat", highlightbackground=panel_border)
        controls_frame.pack(fill="x", padx=0, pady=8)

        tk.Button(controls_frame, text="Iniciar monitoreo", width=18, command=self._iniciar, **button_style).grid(row=0, column=0, padx=4, pady=4)
        tk.Button(controls_frame, text="Detener monitoreo", width=18, command=self._detener, **button_style).grid(row=0, column=1, padx=4, pady=4)
        tk.Button(controls_frame, text="Botón de pánico", width=18, command=self._activar_panico, **button_style).grid(row=1, column=0, padx=4, pady=4)
        tk.Button(controls_frame, text="Simular zona peligrosa", width=18, command=self._simular_zona_peligrosa, **button_style).grid(row=1, column=1, padx=4, pady=4)
        tk.Button(controls_frame, text="Exportar historial", width=18, command=self._exportar_historial, **button_style).grid(row=2, column=0, padx=4, pady=4)
        tk.Button(controls_frame, text="Salir", width=18, command=self._salir, **button_style).grid(row=2, column=1, padx=4, pady=4)
        tk.Button(controls_frame, text="Zoom +", width=18, command=self._zoom_in, **button_style).grid(row=3, column=0, padx=4, pady=4)
        tk.Button(controls_frame, text="Zoom -", width=18, command=self._zoom_out, **button_style).grid(row=3, column=1, padx=4, pady=4)
        tk.Button(controls_frame, text="Llamar 911", width=38, command=self._llamar_911, **button_style).grid(row=4, column=0, columnspan=2, padx=4, pady=4)

        medico_card = tk.LabelFrame(medico_page, text="Médico", padx=12, pady=12, font=label_font, bg=panel_bg, fg=text_color, bd=1, relief="flat", highlightbackground=panel_border)
        medico_card.pack(fill="both", expand=True, padx=0, pady=8)
        tk.Label(medico_card, text="Sube tu historial clínico en PDF para que el médico pueda revisarlo rápidamente.", font=body_font, bg=panel_bg, fg=muted_text, wraplength=360, justify="left").pack(fill="x", pady=(0, 12))
        tk.Button(medico_card, text="Subir historial clínico (PDF)", command=self._subir_pdf_clinico, **button_style).pack(fill="x", padx=4, pady=(0, 8))
        tk.Button(medico_card, text="Ver PDF", command=self._ver_pdf_clinico, **button_style).pack(fill="x", padx=4, pady=(0, 8))
        tk.Label(medico_card, textvariable=self.pdf_path_var, anchor="w", font=body_font, bg=panel_bg, fg=text_color, wraplength=360, justify="left").pack(fill="x", padx=4)

        estado_canvas = tk.Canvas(estado_page, bg=app_bg, highlightthickness=0)
        estado_scrollbar = tk.Scrollbar(estado_page, orient="vertical", command=estado_canvas.yview)
        estado_canvas.configure(yscrollcommand=estado_scrollbar.set)
        estado_scrollbar.pack(side="right", fill="y")
        estado_canvas.pack(side="left", fill="both", expand=True)

        estado_content = tk.Frame(estado_canvas, bg=app_bg)
        estado_content_id = estado_canvas.create_window((0, 0), window=estado_content, anchor="nw")

        def _update_estado_scrollregion(event):
            estado_canvas.configure(scrollregion=estado_canvas.bbox("all"))
        estado_content.bind("<Configure>", _update_estado_scrollregion)
        estado_canvas.bind("<Configure>", lambda event: estado_canvas.itemconfig(estado_content_id, width=event.width))

        def _on_estado_mousewheel(event):
            estado_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        estado_canvas.bind_all("<MouseWheel>", _on_estado_mousewheel)

        estado_box = tk.LabelFrame(estado_content, text="Estado actual", padx=12, pady=12, font=label_font, bg=panel_bg, fg=text_color, bd=1, relief="flat", highlightbackground=panel_border)
        estado_box.pack(fill="both", expand=True, padx=0, pady=(0, 8))

        estado_box.grid_columnconfigure(0, weight=1)
        estado_box.grid_columnconfigure(1, weight=1)

        riesgo_title = tk.Label(estado_box, text="RIESGO ACTUAL", font=label_font, fg="#ffffff", bg="#1d4ed8")
        riesgo_title.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0,4))
        self.riesgo_label = tk.Label(estado_box, textvariable=self.riesgo_var, font=("Segoe UI", 16, "bold"), fg="#0f172a", bg=strong_bg, padx=10, pady=8)
        self.riesgo_label.grid(row=1, column=0, columnspan=2, sticky="we", pady=(0,8), padx=(0,8))

        tk.Label(estado_box, text="UBICACIÓN ACTUAL", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=2, column=0, columnspan=2, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.calle_var, font=body_font, fg=text_color, bg=info_bg, padx=10, pady=10, wraplength=380, justify="left").grid(row=3, column=0, columnspan=2, sticky="we", pady=(0,10))

        tk.Label(estado_box, text="ZONA", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=4, column=0, columnspan=2, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.zona_var, font=body_font, fg=text_color, bg=info_bg, padx=10, pady=10).grid(row=5, column=0, columnspan=2, sticky="we", pady=(0,10))

        tk.Label(estado_box, text="BATERÍA", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=6, column=0, sticky="we", pady=(0,4))
        tk.Label(estado_box, text="SIGNOS", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=6, column=1, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.bateria_var, font=small_font, fg=text_color, bg=stat_bg, padx=8, pady=8).grid(row=7, column=0, sticky="we", pady=(0,10), padx=(0,8))
        tk.Label(estado_box, textvariable=self.estado_var, font=small_font, fg=text_color, bg=stat_bg, padx=8, pady=8).grid(row=7, column=1, sticky="we", pady=(0,10), padx=(0,8))

        self.signos_vitales_var = tk.StringVar(value="Sin datos de signos vitales todavía.")
        self.signos_alertas_var = tk.StringVar(value="No se detectaron anomalías en los signos.")

        tk.Label(estado_box, text="SIGNOS VITALES", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=8, column=0, columnspan=2, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.signos_vitales_var, font=small_font, fg=text_color, bg=info_bg, padx=8, pady=10, wraplength=380, justify="left").grid(row=9, column=0, columnspan=2, sticky="we", pady=(0,10))

        tk.Label(estado_box, text="ANOMALÍAS DETECTADAS", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=10, column=0, columnspan=2, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.signos_alertas_var, font=small_font, fg=text_color, bg=stat_bg, padx=8, pady=10, wraplength=380, justify="left").grid(row=11, column=0, columnspan=2, sticky="we", pady=(0,10))

        tk.Label(estado_box, text="ÚLTIMA LECTURA", font=label_font, fg="#ffffff", bg="#1d4ed8").grid(row=12, column=0, columnspan=2, sticky="we", pady=(0,4))
        tk.Label(estado_box, textvariable=self.ultima_var, font=small_font, fg=text_color, bg=info_bg, padx=8, pady=12, wraplength=360, justify="left").grid(row=13, column=0, columnspan=2, sticky="we", pady=(0,12))

        alerta_label = tk.Label(estado_box, textvariable=self.alerta_var, font=label_font, fg="#ffffff", bg="#dc2626", padx=10, pady=10)
        alerta_label.grid(row=14, column=0, columnspan=2, sticky="we", pady=(0,12))

        tk.Button(estado_box, text="Iniciar monitoreo", width=18, command=self._iniciar, **button_style).grid(row=15, column=0, padx=4, pady=(0, 8), sticky="we")
        tk.Button(estado_box, text="Detener monitoreo", width=18, command=self._detener, **button_style).grid(row=15, column=1, padx=4, pady=(0, 8), sticky="we")
        tk.Button(estado_box, text="Llamada de emergencia", width=38, command=self._llamar_911, **button_style).grid(row=16, column=0, columnspan=2, padx=4, pady=(8, 0), sticky="we")

        map_card = tk.Frame(mapa_page, bg=panel_bg, highlightthickness=0, height=340)
        map_card.pack(fill="both", expand=True, padx=0, pady=(0, 8))
        map_card.pack_propagate(False)

        tk.Label(map_card, text="Mapa de ubicación", font=label_font, bg=panel_bg, fg=text_color, anchor="w").pack(fill="x", padx=12, pady=(10, 6))

        map_frame = tk.Frame(map_card, bg=panel_bg, highlightthickness=0, height=300)
        map_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        map_frame.pack_propagate(False)
        map_frame.grid_rowconfigure(0, weight=1)
        map_frame.grid_columnconfigure(0, weight=1)

        if tkintermapview:
            self.map_widget = tkintermapview.TkinterMapView(map_frame, width=360, height=260, corner_radius=12)
            self.map_widget.grid(row=0, column=0, sticky="nsew")
            self.map_widget.bind("<MouseWheel>", lambda event: "break")
            self.map_widget.bind("<Button-4>", lambda event: "break")
            self.map_widget.bind("<Button-5>", lambda event: "break")
            self.map_widget.add_left_click_map_command(self._on_map_click)
            self.map_widget.set_zoom(12)
            self.map_widget.set_position(19.256928, -99.653165)
            self.map_history = [(19.256928, -99.653165)]
            self.map_path = None
            self.map_marker = None
            self.origin_marker = self.map_widget.set_marker(19.256928, -99.653165, text="Origen")
        else:
            self.map_widget = tk.Canvas(map_frame, bg=panel_bg, highlightthickness=0)
            self.map_widget.grid(row=0, column=0, sticky="nsew")
            self.map_widget.create_text(180, 140, text="Mapa no disponible", fill=text_color, font=("Segoe UI", 14, "bold"))
            self.map_widget.bind("<Button-1>", self._on_map_click_canvas)
            self.map_marker = None

        button_frame = tk.Frame(map_card, bg=panel_bg)
        button_frame.pack(fill="x", padx=12, pady=(0, 10))
        tk.Button(button_frame, text="Tabla de eventos", command=lambda: self._show_page("eventos"), **button_style).pack(fill="x")

        log_card = tk.Frame(eventos_page, bg=panel_bg, highlightthickness=0)
        log_card.pack(fill="both", expand=True, padx=0, pady=(0, 12))

        tk.Label(log_card, text="Registro de eventos", font=label_font, bg=panel_bg, fg=text_color, anchor="w").pack(fill="x", padx=12, pady=(10, 6))

        log_frame = tk.Frame(log_card, bg=panel_bg, highlightthickness=0)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_canvas = tk.Canvas(log_frame, bg=panel_bg, highlightthickness=0)
        self.log_canvas.grid(row=0, column=0, sticky="nsew")

        vscroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_canvas.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        self.log_canvas.configure(yscrollcommand=vscroll.set)

        self.log_inner = tk.Frame(self.log_canvas, bg=panel_bg)
        self._log_window = self.log_canvas.create_window((0, 0), window=self.log_inner, anchor="nw")

        self.log_inner.bind(
            "<Configure>",
            lambda event: self.log_canvas.configure(scrollregion=self.log_canvas.bbox("all"))
        )
        self.log_canvas.bind(
            "<Configure>",
            lambda event: self.log_canvas.itemconfigure(self._log_window, width=event.width)
        )

        self.log_canvas.bind("<Enter>", lambda event: self.log_canvas.focus_set())
        self.log_canvas.bind("<MouseWheel>", lambda event: self.log_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))
        self.log_canvas.bind("<Button-4>", lambda event: self.log_canvas.yview_scroll(-1, "units"))
        self.log_canvas.bind("<Button-5>", lambda event: self.log_canvas.yview_scroll(1, "units"))

        self._show_page("inicio")
        self._append_log("✨ La interfaz está lista. Presiona 'Iniciar monitoreo' para empezar.")

    def _show_page(self, key: str):
        if key in self.pages:
            self.pages[key].tkraise()
        for button_key, button in getattr(self, 'nav_buttons', {}).items():
            button.configure(bg="#22d3ee", fg="#03111f")
        if hasattr(self, 'nav_buttons') and key in self.nav_buttons:
            self.nav_buttons[key].configure(bg="#06b6d4", fg="#ffffff")

    def _append_log(self, texto: str):
        card_bg = "#0d1724"
        card_border = "#165d91"
        badge_bg = "#22d3ee"
        if "ALERTA" in texto or "CRÍTICO" in texto or "SOS" in texto or "⚠️" in texto:
            badge_bg = "#f97316"
        elif "✅" in texto or "✨" in texto:
            badge_bg = "#10b981"

        card = tk.Frame(self.log_inner, bg=card_bg, bd=1, relief="solid", highlightbackground=card_border, highlightthickness=1)
        card.pack(fill="x", pady=(0, 10), padx=(0, 2))

        header = tk.Frame(card, bg=card_bg)
        header.pack(fill="x", padx=10, pady=(10, 0))
        tk.Label(header, text=datetime.now().strftime("%d/%m/%Y %H:%M:%S"), font=("Segoe UI", 8, "italic"), fg="#94a3b8", bg=card_bg).pack(side="left")
        tk.Label(header, text="Evento", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg=badge_bg, padx=8, pady=2).pack(side="right")

        tk.Label(card, text=texto, font=("Segoe UI", 10), fg="#e2e8f0", bg=card_bg, justify="left", wraplength=420).pack(fill="x", padx=10, pady=(6, 10))

        self.log_canvas.update_idletasks()
        self.log_canvas.yview_moveto(1.0)

    def _on_map_click(self, coords):
        self._append_log("📍 Mapa pulsado. Usa 'Tabla de eventos' para ver el historial de eventos.")

    def _on_map_click_canvas(self, event):
        self._append_log("📍 Mapa pulsado. Usa 'Tabla de eventos' para ver el historial de eventos.")

    def _mostrar_eventos_popup(self, coords=None):
        if self.event_popup and self.event_popup.winfo_exists():
            self.event_popup.lift()
            self.event_popup.focus_force()
            return

        popup = tk.Toplevel(self.root)
        popup.title("Eventos del mapa")
        popup.geometry("900x460")
        popup.configure(bg="#050816")
        popup.resizable(True, True)
        popup.transient(self.root)
        popup.grab_set()

        header_bg = "#0b1229"
        text_color = "#e0f2fe"
        row_bg = "#08111f"

        header = tk.Frame(popup, bg=header_bg, pady=12)
        header.pack(fill="x", padx=12, pady=(12, 0))
        tk.Label(header, text="Tabla de eventos", font=("Segoe UI", 16, "bold"), bg=header_bg, fg=text_color).pack(side="left")

        tk.Label(popup, text="Haz clic en el mapa para ver el detalle de los eventos registrados.", font=("Segoe UI", 11), bg="#050816", fg="#7dd3fc", anchor="w").pack(fill="x", padx=12, pady=(10, 8))

        if coords is not None:
            lat, lon = coords
            tk.Label(popup, text=f"Coordenadas del clic: lat={lat:.5f}, lon={lon:.5f}", font=("Segoe UI", 10, "bold"), bg="#050816", fg="#e0f2fe", anchor="w").pack(fill="x", padx=12, pady=(0, 8))

        table_frame = tk.Frame(popup, bg="#050816")
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        tree = ttk.Treeview(table_frame, columns=("fecha", "zona", "riesgo", "estado", "bateria", "ubicacion"), show="headings")
        tree.heading("fecha", text="Fecha")
        tree.heading("zona", text="Zona")
        tree.heading("riesgo", text="Riesgo")
        tree.heading("estado", text="Estado")
        tree.heading("bateria", text="Batería")
        tree.heading("ubicacion", text="Ubicación")

        tree.column("fecha", width=160, anchor="center")
        tree.column("zona", width=200, anchor="w")
        tree.column("riesgo", width=100, anchor="center")
        tree.column("estado", width=120, anchor="center")
        tree.column("bateria", width=90, anchor="center")
        tree.column("ubicacion", width=180, anchor="w")

        tree.grid(row=0, column=0, sticky="nsew")

        vscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        vscroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=vscroll.set)

        style = ttk.Style(popup)
        style.configure("Treeview", background=row_bg, fieldbackground=row_bg, foreground=text_color, rowheight=28)
        style.configure("Treeview.Heading", background="#0f172a", foreground="#e0f2fe")
        style.map("Treeview", background=[("selected", "#1d4ed8")], foreground=[("selected", "#ffffff")])

        if not self.event_history:
            tk.Label(popup, text="Sin eventos registrados aún.", font=("Segoe UI", 11), bg="#050816", fg="#7dd3fc").pack(fill="x", padx=12, pady=(0, 12))
        else:
            for evento in reversed(self.event_history):
                tree.insert(
                    "",
                    tk.END,
                    values=(
                        evento["timestamp"][:19].replace("T", " "),
                        evento["zona"],
                        evento["riesgo"],
                        evento["estado_signos"],
                        f"{evento['bateria']:.0f}%",
                        f"{evento['ubicacion']['latitud']:.5f}, {evento['ubicacion']['longitud']:.5f}",
                    ),
                )

        footer = tk.Frame(popup, bg=header_bg)
        footer.pack(fill="x", padx=12, pady=12)
        tk.Button(footer, text="Cerrar", command=popup.destroy, bg="#22d3ee", fg="#03111f", font=("Segoe UI", 10, "bold"), relief="flat", bd=0, cursor="hand2").pack(side="right")

        def on_close():
            self.event_popup = None
            popup.destroy()

        popup.protocol("WM_DELETE_WINDOW", on_close)
        self.event_popup = popup

    def _abrir_registro_usuario(self):
        if self.registro_popup and self.registro_popup.winfo_exists():
            self.registro_popup.lift()
            self.registro_popup.focus_force()
            return

        self.registro_popup = tk.Toplevel(self.root)
        self.registro_popup.title("Registrar usuario")
        self.registro_popup.geometry("440x620")
        self.registro_popup.configure(bg="#050816")
        self.registro_popup.resizable(False, False)
        self.registro_popup.transient(self.root)
        self.registro_popup.grab_set()

        header = tk.Frame(self.registro_popup, bg="#0b1229", pady=12)
        header.pack(fill="x", padx=12, pady=(12, 0))
        tk.Label(header, text="Registro de usuario", font=("Segoe UI", 16, "bold"), bg="#0b1229", fg="#e0f2fe").pack(side="left")

        form_frame = tk.Frame(self.registro_popup, bg="#050816")
        form_frame.pack(fill="both", expand=True, padx=12, pady=12)

        def crear_campo(label_text, row, default=""):
            tk.Label(form_frame, text=label_text, anchor="w", font=("Segoe UI", 10, "bold"), bg="#050816", fg="#7dd3fc").grid(row=row, column=0, sticky="w", pady=(8, 2))
            entry = tk.Entry(form_frame, font=("Segoe UI", 10), bg="#0f172a", fg="#e0f2fe", insertbackground="#e0f2fe")
            entry.grid(row=row, column=1, sticky="we", padx=(8, 0), pady=(8, 2))
            entry.insert(0, default)
            return entry

        form_frame.grid_columnconfigure(1, weight=1)
        nombre_entry = crear_campo("Nombre completo", 0, self.usuario.nombre)
        edad_entry = crear_campo("Edad", 1, str(self.usuario.edad))
        curp_entry = crear_campo("CURP", 2, self.usuario.curp)
        calle_entry = crear_campo("Calle", 3, self.usuario.calle)
        numero_entry = crear_campo("Número", 4, self.usuario.numero)
        colonia_entry = crear_campo("Colonia", 5, self.usuario.colonia)
        cp_entry = crear_campo("C.P.", 6, self.usuario.cp)

        tk.Label(form_frame, text="Municipio", anchor="w", font=("Segoe UI", 10, "bold"), bg="#050816", fg="#7dd3fc").grid(row=7, column=0, sticky="w", pady=(8, 2))
        tk.Label(form_frame, text="Metepec", anchor="w", font=("Segoe UI", 10), bg="#050816", fg="#e0f2fe").grid(row=7, column=1, sticky="w", padx=(8, 0), pady=(8, 2))
        tk.Label(form_frame, text="Estado", anchor="w", font=("Segoe UI", 10, "bold"), bg="#050816", fg="#7dd3fc").grid(row=8, column=0, sticky="w", pady=(8, 2))
        tk.Label(form_frame, text="Estado de México", anchor="w", font=("Segoe UI", 10), bg="#050816", fg="#e0f2fe").grid(row=8, column=1, sticky="w", padx=(8, 0), pady=(8, 2))

        condiciones_entry = crear_campo("Condiciones médicas", 9, ", ".join(self.usuario.condiciones_medicas))
        medicamentos_entry = crear_campo("Medicamentos", 10, ", ".join(self.usuario.medicamentos))

        photo_frame = tk.Frame(form_frame, bg="#050816")
        photo_frame.grid(row=11, column=0, columnspan=2, pady=(12, 0), sticky="we")
        photo_canvas = tk.Canvas(photo_frame, width=100, height=100, bg="#15263b", highlightthickness=0)
        photo_canvas.create_text(50, 50, text="Foto", fill="#e0f2fe", font=("Segoe UI", 10, "bold"))
        photo_canvas.pack(side="left")
        self.registro_foto_label = tk.Label(photo_frame, text="Sin foto", font=("Segoe UI", 10), bg="#050816", fg="#e0f2fe")
        self.registro_foto_label.pack(side="left", padx=12)

        tk.Button(photo_frame, text="Tomar foto", command=lambda: self._tomar_foto(photo_canvas, self.registro_foto_label), **{"font": ("Segoe UI", 10, "bold"), "bg": "#22d3ee", "fg": "#03111f", "relief": "flat", "bd": 0, "cursor": "hand2"}).pack(side="right")

        button_frame = tk.Frame(self.registro_popup, bg="#050816")
        button_frame.pack(fill="x", padx=12, pady=(8, 12))
        tk.Button(button_frame, text="Guardar", command=lambda: self._guardar_usuario(
            nombre_entry, edad_entry, curp_entry, calle_entry, numero_entry,
            colonia_entry, cp_entry, condiciones_entry, medicamentos_entry), **{"font": ("Segoe UI", 10, "bold"), "bg": "#22d3ee", "fg": "#03111f", "relief": "flat", "bd": 0, "cursor": "hand2"}).pack(side="right", padx=(8, 0))
        tk.Button(button_frame, text="Cancelar", command=self.registro_popup.destroy, **{"font": ("Segoe UI", 10, "bold"), "bg": "#0f172a", "fg": "#e0f2fe", "relief": "flat", "bd": 0, "cursor": "hand2"}).pack(side="right")

        def on_close():
            if self.registro_popup and self.registro_popup.winfo_exists():
                self.registro_popup.destroy()
            self.registro_popup = None

        self.registro_popup.protocol("WM_DELETE_WINDOW", on_close)

    def _tomar_foto(self, canvas: tk.Canvas, label: tk.Label):
        if cv2 is None:
            messagebox.showwarning("Cámara no disponible", "No se puede tomar foto porque OpenCV no está instalado.")
            return

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if hasattr(cv2, 'CAP_DSHOW') else 0)
        if not cap.isOpened():
            messagebox.showerror("Cámara no conectada", "No se detectó cámara web. Verifica que esté conectada e intenta nuevamente.")
            return

        ret, frame = cap.read()
        cap.release()
        if not ret:
            messagebox.showerror("Error de captura", "No se pudo tomar la foto desde la cámara.")
            return

        ruta_foto = os.path.join(tempfile.gettempdir(), f"centinela_foto_{int(time.time())}.png")
        cv2.imwrite(ruta_foto, frame)
        self.usuario.foto_url = ruta_foto
        self._mostrar_foto_en_canvas(canvas, label)

    def _mostrar_foto_en_canvas(self, canvas: tk.Canvas, label: tk.Label):
        canvas.delete("all")
        if self.usuario.foto_url and os.path.exists(self.usuario.foto_url):
            try:
                if Image and ImageTk:
                    img = Image.open(self.usuario.foto_url)
                    img = img.resize((100, 100), Image.LANCZOS if hasattr(Image, 'LANCZOS') else Image.ANTIALIAS)
                    self.user_photo_img = ImageTk.PhotoImage(img)
                else:
                    self.user_photo_img = tk.PhotoImage(file=self.usuario.foto_url)
                canvas.create_image(50, 50, image=self.user_photo_img)
                label.config(text="Foto tomada")
            except Exception:
                canvas.create_rectangle(12, 12, 88, 88, fill="#0ea5e9", outline="#22d3ee")
                canvas.create_text(50, 50, text="OK", fill="#ffffff", font=("Segoe UI", 14, "bold"))
                label.config(text="Foto tomada")
        else:
            canvas.create_text(50, 50, text="Foto", fill="#e0f2fe", font=("Segoe UI", 10, "bold"))
            label.config(text="Sin foto")

    def _guardar_usuario(self, nombre_entry, edad_entry, curp_entry, calle_entry, numero_entry, colonia_entry, cp_entry, condiciones_entry, medicamentos_entry):
        self.usuario.nombre = nombre_entry.get().strip() or self.usuario.nombre
        try:
            self.usuario.edad = int(edad_entry.get().strip() or self.usuario.edad)
        except ValueError:
            self.usuario.edad = self.usuario.edad
        self.usuario.curp = curp_entry.get().strip() or self.usuario.curp
        self.usuario.calle = calle_entry.get().strip() or self.usuario.calle
        self.usuario.numero = numero_entry.get().strip() or self.usuario.numero
        self.usuario.colonia = colonia_entry.get().strip() or self.usuario.colonia
        self.usuario.cp = cp_entry.get().strip() or self.usuario.cp
        self.usuario.condiciones_medicas = [cond.strip() for cond in condiciones_entry.get().split(",") if cond.strip()]
        self.usuario.medicamentos = [med.strip() for med in medicamentos_entry.get().split(",") if med.strip()]

        self._actualizar_usuario_ui()
        if self.registro_popup and self.registro_popup.winfo_exists():
            self.registro_popup.destroy()
            self.registro_popup = None
        self._show_page("usuario")
        self._append_log("📝 Usuario registrado y actualizado correctamente.")

    def _actualizar_usuario_ui(self):
        self.user_name_label.config(text=f"Nombre: {self.usuario.nombre}")
        self.user_age_label.config(text=f"Edad: {self.usuario.edad} años")
        self.user_curp_label.config(text=f"CURP: {self.usuario.curp}")
        self.user_device_label.config(text=f"Dispositivo: {self.usuario.tipo_dispositivo.upper()} — {self.usuario.dispositivo_id}")
        self.user_blood_label.config(text=f"Grupo sanguíneo: {self.usuario.grupo_sanguineo}")
        self.user_address1_label.config(text=f"Calle: {self.usuario.calle} #{self.usuario.numero}")
        self.user_address2_label.config(text=f"Colonia: {self.usuario.colonia}")
        self.user_address3_label.config(text=f"Municipio: {self.usuario.municipio}, {self.usuario.estado}")
        self.user_address4_label.config(text=f"C.P.: {self.usuario.cp}")
        for label in getattr(self, "user_conditions", []):
            label.destroy()
        self.user_conditions = []
        condiciones = self.usuario.condiciones_medicas or ["Sin enfermedades registradas"]
        clinic_frame = self.user_medications_label.master
        for condicion in condiciones:
            label = tk.Label(clinic_frame, text=f"• {condicion}", anchor="w", font=("Segoe UI", 11), bg="#0b1229", fg="#e0f2fe")
            label.pack(fill="x", pady=(0,2), before=self.user_medications_label)
            self.user_conditions.append(label)
        self.user_medications_label.config(text=", ".join(self.usuario.medicamentos) if self.usuario.medicamentos else "Ninguno")
        self._mostrar_foto_en_canvas(self.user_photo_canvas, self.user_photo_label)

    def _enqueue_log(self, texto: str):
        self.queue.put(("log", texto))

    def _enqueue_event(self, evento: dict):
        self.queue.put(("event", evento))

    def _procesar_cola(self):
        try:
            while True:
                tipo, payload = self.queue.get_nowait()
                if tipo == "log":
                    self._append_log(payload)
                elif tipo == "event":
                    self._actualizar_estado(payload)
        except Empty:
            pass
        self.root.after(200, self._procesar_cola)

    def _zoom_in(self):
        if not tkintermapview or not hasattr(self, "map_widget") or self.map_widget is None:
            return
        try:
            self.map_widget.set_zoom(min(self.map_widget.max_zoom, self.map_widget.zoom + 1))
        except Exception:
            pass

    def _zoom_out(self):
        if not tkintermapview or not hasattr(self, "map_widget") or self.map_widget is None:
            return
        try:
            self.map_widget.set_zoom(max(self.map_widget.min_zoom, self.map_widget.zoom - 1))
        except Exception:
            pass

    def _actualizar_estado(self, datos: dict):
        self.riesgo_var.set(f"{datos['riesgo_emoji']} {datos['riesgo']}")
        self.zona_var.set(datos['zona'])
        self.bateria_var.set(f"{datos['bateria']:.0f}%")
        self.estado_var.set(datos['estado_signos'])
        self.ultima_var.set(datos['timestamp'])
        self.event_history.append(datos)
        if tkintermapview and self.map_widget:
            nueva_coord = (datos['ubicacion']['latitud'], datos['ubicacion']['longitud'])
            self.map_widget.set_position(datos['ubicacion']['latitud'], datos['ubicacion']['longitud'])
            if not self.map_history or self.map_history[-1] != nueva_coord:
                self.map_history.append(nueva_coord)

            if self.map_path:
                try:
                    self.map_path.delete()
                except Exception:
                    pass
            try:
                self.map_path = self.map_widget.set_path(self.map_history, color="#30bced", width=4)
            except Exception:
                self.map_path = None

            if self.map_marker:
                try:
                    self.map_marker.set_position(datos['ubicacion']['latitud'], datos['ubicacion']['longitud'])
                    self.map_marker.set_text(f"{datos['ubicacion']['calle']}")
                except Exception:
                    self.map_marker.delete()
                    self.map_marker = self.map_widget.set_marker(
                        datos['ubicacion']['latitud'],
                        datos['ubicacion']['longitud'],
                        text=f"{datos['ubicacion']['calle']}"
                    )
            else:
                self.map_marker = self.map_widget.set_marker(
                    datos['ubicacion']['latitud'],
                    datos['ubicacion']['longitud'],
                    text=f"{datos['ubicacion']['calle']}"
                )

        signos = datos.get("signos_vitales")
        if datos.get("ubicacion"):
            ubicacion = datos["ubicacion"]
            calle = ubicacion.get("calle") or "Calle desconocida"
            self.calle_var.set(
                f"Calle actual: {calle} — {ubicacion['latitud']:.5f}, {ubicacion['longitud']:.5f}"
            )
        else:
            self.calle_var.set("Calle actual: Calle desconocida")

        if signos:
            signos_text = (
                f"FC: {signos['frecuencia_cardiaca']} lpm | "
                f"SpO2: {signos['saturacion_oxigeno']:.1f}% | "
                f"Temp: {signos['temperatura_corporal']:.1f}°C | "
                f"PA: {signos['presion_sistolica']}/{signos['presion_diastolica']} mmHg | "
                f"Actividad: {signos['nivel_actividad']}")
            self.signos_vitales_var.set(signos_text)
        else:
            self.signos_vitales_var.set("Sin datos de signos vitales todavía.")

        alertas = datos.get("alertas") or []
        if alertas:
            self.signos_alertas_var.set("\n".join(f"• {alerta}" for alerta in alertas))
        else:
            self.signos_alertas_var.set("No se detectaron anomalías en los signos.")

        if datos.get("requiere_emergencia"):
            self.alerta_var.set("ALERTA CRÍTICA: ACTÚA INMEDIATAMENTE")
            self._play_alarm()
        elif alertas:
            self.alerta_var.set("Atención: se ha detectado un evento de riesgo")
        else:
            self.alerta_var.set("Sistema estable")

    def _iniciar(self):
        if not self.guardian.activo:
            self.guardian.iniciar()
            self.status_var.set("Monitoreo activo")
            self.menu.set_estado("● Activo", "#10b981")
            self._append_log("✅ El monitoreo ya está activo y cuidando la seguridad.")
        self._show_page("estado")

    def _detener(self):
        if self.guardian.activo:
            self.guardian.detener()
            self.status_var.set("Monitoreo detenido")
            self.menu.set_estado("● Detenido", "#94a3b8")
            self._append_log("⏸️ El monitoreo se detuvo. Puedes volver a iniciarlo cuando quieras.")
        self._show_page("estado")

    def _activar_panico(self):
        self._append_log("🆘 Se activó el botón de pánico. La ayuda se está enviando.")
        self.guardian.activar_panico()
        self._show_page("estado")

    def _simular_zona_peligrosa(self):
        self.guardian.sensor.simular_emergencia("zona_peligrosa")
        self._append_log("🎭 Se simuló una situación de riesgo para revisar el sistema.")
        self._show_page("estado")

    def _play_alarm(self):
        self._append_log("🔊 Se activó una alerta sonora para llamar tu atención.")
        try:
            if winsound:
                for frecuencia in [900, 1200, 1500]:
                    winsound.Beep(frecuencia, 200)
            else:
                self.root.bell()
        except Exception:
            self.root.bell()

    def _exportar_historial(self):
        ruta = self.guardian.exportar_historial()
        self._append_log(f"📁 El historial se guardó correctamente en: {ruta}")

    def _llamar_911(self):
        try:
            if os.name == "nt":
                os.startfile("tel:911")
            else:
                webbrowser.open("tel:911")
            self._append_log("📞 Iniciando llamada a 911...")
        except Exception:
            self._append_log("⚠️ No se pudo iniciar la llamada automáticamente. Marca 911 manualmente.")
            messagebox.showinfo("Llamada de emergencia", "No se pudo iniciar la llamada automática. Por favor, marca 911 manualmente.")

    def _subir_pdf_clinico(self):
        ruta = filedialog.askopenfilename(filetypes=[("PDF", "*.pdf")], title="Seleccionar historial clínico PDF")
        if ruta:
            self.pdf_loaded_path = ruta
            self.pdf_path_var.set(f"PDF cargado: {ruta}")
            self._append_log(f"📄 Historial clínico cargado: {os.path.basename(ruta)}")

    def _ver_pdf_clinico(self):
        if not self.pdf_loaded_path:
            messagebox.showwarning("Ver PDF", "No hay ningún historial clínico cargado. Primero selecciona un PDF.")
            return
        try:
            if os.name == "nt":
                os.startfile(self.pdf_loaded_path)
            else:
                webbrowser.open(f"file://{self.pdf_loaded_path}")
            self._append_log(f"📄 Abriendo PDF médico: {os.path.basename(self.pdf_loaded_path)}")
        except Exception as exc:
            self._append_log(f"⚠️ No se pudo abrir el PDF: {exc}")
            messagebox.showerror("Error al abrir PDF", "No se pudo abrir el archivo PDF seleccionado.")

    def _salir(self):
        if self.guardian.activo:
            self.guardian.detener()
        self.root.quit()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    InterfazGuardianWear().run()

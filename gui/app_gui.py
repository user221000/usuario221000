"""Interfaz gráfica CustomTkinter para Método Base."""
import os
import re
import threading
import webbrowser
import urllib.parse
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageFilter, ImageEnhance

from utils.helpers import resource_path, abrir_carpeta_pdf
from config.constantes import (
    FACTORES_ACTIVIDAD, NIVELES_ACTIVIDAD, OBJETIVOS_VALIDOS, CARPETA_SALIDA,
)
from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional
from core.generador_planes import ConstructorPlanNuevo
from core.exportador_salida import GeneradorPDFProfesional


class GymApp(ctk.CTk):
    """Aplicacion principal con CustomTkinter - Diseño profesional moderno."""
    
    # Paleta de colores
    COLOR_BG = "#121212"
    COLOR_CARD = "#1E1E1E"
    COLOR_PRIMARY = "#7B2D8E"
    COLOR_PRIMARY_HOVER = "#9B3DB0"
    COLOR_SECONDARY = "#D4A84B"
    COLOR_SECONDARY_HOVER = "#E4B85B"
    COLOR_BORDER = "#444444"
    COLOR_TEXT = "#FFFFFF"
    COLOR_TEXT_MUTED = "#888888"
    COLOR_INPUT_BG = "#2A2A2A"
    COLOR_SUCCESS = "#2B5B2B"
    COLOR_SUCCESS_HOVER = "#3D7A3D"
    
    def __init__(self):
        super().__init__()

        self.title("Método Base - Consultoría Hernández")
        self.geometry("820x900")
        self.resizable(False, False)
        self.configure(fg_color=self.COLOR_BG)
        ctk.set_appearance_mode("Dark")
        
        self.ultimo_pdf = None
        self.ultima_ruta_pdf = None
        
        # Contenedor principal con scroll
        self.main_container = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=self.COLOR_PRIMARY,
            scrollbar_button_hover_color=self.COLOR_PRIMARY_HOVER
        )
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ═══════════════ HEADER / BRANDING ═══════════════
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(20, 4))
        
        self.title_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.title_container.pack()
        
        self._crear_header_watermark(self.title_container)
        
        self.lbl_titulo = ctk.CTkLabel(
            self.title_container, text="Metodo Base",
            font=ctk.CTkFont(family="Segoe UI", size=42, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        self.lbl_titulo.pack(pady=(0, 2))

        self.lbl_subtitulo = ctk.CTkLabel(
            self.header_frame, text="Fitness Gym Real del Valle",
            font=ctk.CTkFont(family="Segoe UI", size=15),
            text_color=self.COLOR_SECONDARY
        )
        self.lbl_subtitulo.pack(pady=(0, 4))

        self.lbl_contexto = ctk.CTkLabel(
            self.header_frame, text="Powered by C. H.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_contexto.pack(pady=(0, 10))
        
        self.separator = ctk.CTkFrame(self.main_container, height=2, fg_color=self.COLOR_PRIMARY)
        self.separator.pack(fill="x", padx=60, pady=(0, 12))

        # ═══════════════ SECCIÓN 1: DATOS DEL CLIENTE ═══════════════
        self.section_cliente = self._crear_seccion("Datos del Cliente", "👤")
        
        self.entry_nombre = self._crear_input_full(
            self.section_cliente, "Nombre completo", "Ej: Oscar Hernández", row=0
        )
        
        self.entry_telefono, self.entry_edad = self._crear_input_duo(
            self.section_cliente,
            "Teléfono", "Ej: 5213312345678",
            "Edad", "Ej: 25", row=1
        )

        # ═══════════════ SECCIÓN 2: MEDIDAS CORPORALES ═══════════════
        self.section_medidas = self._crear_seccion("Medidas Corporales", "⚖")
        
        self.entry_peso, self.entry_estatura = self._crear_input_duo(
            self.section_medidas,
            "Peso (kg)", "Ej: 80.5",
            "Estatura (cm)", "Ej: 175", row=0
        )
        
        self.entry_grasa = self._crear_input_full(
            self.section_medidas, "Grasa corporal (%)", "Ej: 18", row=1
        )

        # ═══════════════ SECCIÓN 3: PERFIL DE ENTRENAMIENTO ═══════════════
        self.section_perfil = self._crear_seccion("Perfil de Entrenamiento", "🏋")
        
        self.combo_actividad, self.combo_objetivo = self._crear_combo_duo(
            self.section_perfil,
            "Actividad", list(NIVELES_ACTIVIDAD), "moderada",
            "Objetivo", list(OBJETIVOS_VALIDOS), "mantenimiento", row=0
        )

        # ═══════════════ BOTONES DE ACCIÓN ═══════════════
        self.buttons_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.buttons_frame.pack(fill="x", padx=40, pady=(20, 12))
        
        self.btn_shadow = ctk.CTkFrame(
            self.buttons_frame, fg_color="#5a1e6a",
            corner_radius=12, height=68,
        )
        self.btn_shadow.pack(fill="x", pady=(0, 18), ipady=0)
        self.btn_shadow.pack_propagate(False)

        self.btn_procesar = ctk.CTkButton(
            self.btn_shadow, text="GENERAR PLAN Y PDF",
            command=self._on_procesar_click, height=60, corner_radius=12,
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            fg_color=self.COLOR_PRIMARY, hover_color=self.COLOR_PRIMARY_HOVER,
            border_width=2, border_color=self.COLOR_PRIMARY_HOVER,
            text_color=self.COLOR_TEXT
        )
        self.btn_procesar.pack(fill="x", padx=2, pady=2, ipady=2)
        
        self.secondary_buttons = ctk.CTkFrame(self.buttons_frame, fg_color="transparent")
        self.secondary_buttons.pack(fill="x")
        self.secondary_buttons.grid_columnconfigure(0, weight=1)
        self.secondary_buttons.grid_columnconfigure(1, weight=1)

        self.btn_whatsapp = ctk.CTkButton(
            self.secondary_buttons, text="Enviar por WhatsApp",
            command=self.enviar_por_whatsapp, state="disabled",
            height=36, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLOR_SUCCESS, hover_color=self.COLOR_SUCCESS_HOVER,
            border_width=1, border_color=self.COLOR_SUCCESS_HOVER,
            text_color=self.COLOR_TEXT
        )
        self.btn_whatsapp.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=0)

        self.btn_abrir_pdf = ctk.CTkButton(
            self.secondary_buttons, text="Abrir carpeta de PDF",
            command=abrir_carpeta_pdf, height=36, corner_radius=6,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color="transparent", hover_color=self.COLOR_CARD,
            border_width=1, border_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT_MUTED
        )
        self.btn_abrir_pdf.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=0)

        # ═══════════════ REGISTRO DE OPERACIONES ═══════════════
        self.log_frame = ctk.CTkFrame(
            self.main_container, fg_color=self.COLOR_CARD,
            corner_radius=10, border_width=1, border_color=self.COLOR_BORDER
        )
        self.log_frame.pack(fill="x", padx=40, pady=(16, 24))
        
        self.lbl_status = ctk.CTkLabel(
            self.log_frame, text="Registro de Operaciones", anchor="w",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_status.pack(padx=16, pady=(12, 4), anchor="w")
        
        self.textbox_log = ctk.CTkTextbox(
            self.log_frame, height=100, corner_radius=6,
            fg_color=self.COLOR_INPUT_BG, border_width=0,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.textbox_log.pack(padx=12, pady=(0, 12), fill="x")
        
        self._log("Sistema listo. Esperando datos del cliente...")

    # ───── Helpers de creación de UI ─────

    def _crear_seccion(self, titulo, icono=""):
        card = ctk.CTkFrame(
            self.main_container, fg_color=self.COLOR_CARD,
            corner_radius=12, border_width=1, border_color=self.COLOR_BORDER
        )
        card.pack(fill="x", padx=40, pady=8)
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(14, 8))
        
        if icono:
            lbl_icono = ctk.CTkLabel(
                header, text=icono,
                font=ctk.CTkFont(family="Segoe UI", size=14),
                text_color=self.COLOR_PRIMARY, anchor="w"
            )
            lbl_icono.pack(side="left", padx=(0, 8))
        
        lbl_titulo = ctk.CTkLabel(
            header, text=titulo,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=self.COLOR_SECONDARY, anchor="w"
        )
        lbl_titulo.pack(side="left")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=8, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        content.grid_columnconfigure(3, weight=1)
        
        return content
    
    def _crear_label_campo(self, parent, texto, fila, col=0):
        label = ctk.CTkLabel(
            parent, text=texto,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT, anchor="w"
        )
        label.grid(row=fila, column=col, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        return label
    
    def _crear_input_full(self, parent, label_text, placeholder, row):
        base_row = row * 2
        self._crear_label_campo(parent, label_text, base_row, col=0)
        
        entry = ctk.CTkEntry(
            parent, placeholder_text=placeholder, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry.grid(row=base_row + 1, column=0, columnspan=4, padx=16, pady=(0, 8), sticky="ew")
        return entry
    
    def _crear_input_duo(self, parent, label1, placeholder1, label2, placeholder2, row):
        base_row = row * 2
        
        lbl1 = ctk.CTkLabel(parent, text=label1, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl1.grid(row=base_row, column=0, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        lbl2 = ctk.CTkLabel(parent, text=label2, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl2.grid(row=base_row, column=2, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        entry1 = ctk.CTkEntry(
            parent, placeholder_text=placeholder1, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry1.grid(row=base_row + 1, column=0, columnspan=2, padx=(16, 8), pady=(0, 8), sticky="ew")
        
        entry2 = ctk.CTkEntry(
            parent, placeholder_text=placeholder2, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            fg_color=self.COLOR_INPUT_BG,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            placeholder_text_color=self.COLOR_TEXT_MUTED
        )
        entry2.grid(row=base_row + 1, column=2, columnspan=2, padx=(8, 16), pady=(0, 8), sticky="ew")
        
        return entry1, entry2
    
    def _crear_combo_duo(self, parent, label1, values1, default1, label2, values2, default2, row):
        base_row = row * 2
        
        lbl1 = ctk.CTkLabel(parent, text=label1, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl1.grid(row=base_row, column=0, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        lbl2 = ctk.CTkLabel(parent, text=label2, font=ctk.CTkFont(family="Segoe UI", size=12),
                           text_color=self.COLOR_TEXT, anchor="w")
        lbl2.grid(row=base_row, column=2, columnspan=2, padx=(16, 4), pady=(8, 2), sticky="w")
        
        combo1 = ctk.CTkComboBox(
            parent, values=values1, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            button_color=self.COLOR_PRIMARY, button_hover_color=self.COLOR_PRIMARY_HOVER,
            dropdown_fg_color=self.COLOR_CARD, dropdown_hover_color=self.COLOR_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        combo1.grid(row=base_row + 1, column=0, columnspan=2, padx=(16, 8), pady=(0, 8), sticky="ew")
        combo1.set(default1)
        
        combo2 = ctk.CTkComboBox(
            parent, values=values2, height=38, corner_radius=8,
            border_width=1, border_color=self.COLOR_BORDER,
            button_color=self.COLOR_PRIMARY, button_hover_color=self.COLOR_PRIMARY_HOVER,
            dropdown_fg_color=self.COLOR_CARD, dropdown_hover_color=self.COLOR_PRIMARY,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            dropdown_font=ctk.CTkFont(family="Segoe UI", size=12)
        )
        combo2.grid(row=base_row + 1, column=2, columnspan=2, padx=(8, 16), pady=(0, 8), sticky="ew")
        combo2.set(default2)
        
        return combo1, combo2

    def _crear_header_watermark(self, parent):
        try:
            logo_path = resource_path("assets/logo.png")
            if not os.path.exists(logo_path):
                return
            
            logo_img = Image.open(logo_path)
            watermark_size = 120
            logo_img = logo_img.resize((watermark_size, watermark_size), Image.Resampling.LANCZOS)
            logo_img = logo_img.filter(ImageFilter.GaussianBlur(radius=1.5))
            
            if logo_img.mode == 'RGBA':
                alpha = logo_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(0.07)
                logo_img.putalpha(alpha)
            else:
                logo_img = logo_img.convert('RGBA')
                alpha = logo_img.split()[3]
                alpha = ImageEnhance.Brightness(alpha).enhance(0.07)
                logo_img.putalpha(alpha)
            
            self.header_watermark_photo = ImageTk.PhotoImage(logo_img)
            
            from tkinter import Label
            self.header_watermark_label = Label(
                parent._canvas if hasattr(parent, '_canvas') else parent,
                image=self.header_watermark_photo,
                bg=self.COLOR_BG, borderwidth=0
            )
            self.header_watermark_label.place(relx=0.5, rely=0.5, anchor="center")
        except Exception:
            pass

    # ───── Lógica de negocio ─────

    def _log(self, mensaje):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.textbox_log.insert("end", f"[{timestamp}] {mensaje}\n")
        self.textbox_log.see("end")

    def _on_procesar_click(self):
        self.btn_procesar.configure(state="disabled")
        self._show_spinner_on_button()
        thread = threading.Thread(target=self._procesar_datos)
        thread.start()

    def _procesar_datos(self):
        try:
            self._log("Iniciando procesamiento...")
            
            nombre = self.entry_nombre.get().strip()
            if not nombre:
                raise ValueError("El nombre es obligatorio")
            telefono = self.entry_telefono.get().strip()
            if telefono:
                if not telefono.isdigit():
                    raise ValueError("Telefono invalido: solo numeros, sin espacios ni simbolos")
                if len(telefono) < 10:
                    raise ValueError("Telefono invalido: debe tener al menos 10 digitos")
            edad = int(self.entry_edad.get())
            if edad < 1:
                raise ValueError("Edad invalida: debe ser mayor a 0 anos")
            peso = float(self.entry_peso.get())
            if peso < 20:
                raise ValueError("Peso invalido: el peso minimo permitido es 20 kg")
            if peso > 155:
                raise ValueError("Peso invalido: el peso maximo permitido es 155 kg")
            estatura = float(self.entry_estatura.get())
            grasa = float(self.entry_grasa.get())
            if grasa < 5:
                raise ValueError("Grasa corporal invalida: el porcentaje minimo permitido es 5%")
            actividad = self.combo_actividad.get()
            objetivo = self.combo_objetivo.get()
            
            cliente = ClienteEvaluacion(
                nombre=nombre,
                telefono=telefono if telefono else None,
                edad=edad, peso_kg=peso, estatura_cm=estatura,
                grasa_corporal_pct=grasa, nivel_actividad=actividad,
                objetivo=objetivo
            )
            cliente.factor_actividad = FACTORES_ACTIVIDAD.get(actividad, 1.2)
            self._log(f"Cliente creado: {cliente.nombre} ({cliente.objetivo})")
            
            cliente = MotorNutricional.calcular_motor(cliente)
            self._log(f"TMB={cliente.tmb:.0f}, GET={cliente.get_total:.0f}, Kcal={cliente.kcal_objetivo:.0f}")
            
            dir_planes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "planes")
            os.makedirs(dir_planes, exist_ok=True)
            plan = ConstructorPlanNuevo.construir(cliente, plan_numero=1, directorio_planes=dir_planes)
            self._log("Plan nutricional estructurado correctamente.")
            
            if not os.path.exists(CARPETA_SALIDA):
                os.makedirs(CARPETA_SALIDA)
            fecha = datetime.now().strftime("%Y-%m-%d")
            nombre_cliente_sanitizado = re.sub(r'[^a-zA-Z0-9_]', '', cliente.nombre.replace(" ", "_"))
            carpeta_cliente = os.path.join(CARPETA_SALIDA, nombre_cliente_sanitizado)
            os.makedirs(carpeta_cliente, exist_ok=True)
            hora = datetime.now().strftime("%H-%M-%S")
            nombre_pdf = f"{nombre_cliente_sanitizado}_{fecha}_{hora}.pdf"
            ruta_pdf_completa = os.path.join(carpeta_cliente, nombre_pdf)
            
            generador = GeneradorPDFProfesional(ruta_pdf_completa)
            ruta_pdf = generador.generar(cliente, plan)
            self.ultimo_pdf = ruta_pdf if ruta_pdf and os.path.exists(ruta_pdf) else None
            
            self.after(0, lambda: self.btn_abrir_pdf.configure(state="normal" if self.ultimo_pdf else "disabled"))
            self.after(0, lambda: self.btn_whatsapp.configure(state="normal" if self.ultimo_pdf else "disabled"))
            
            if self.ultimo_pdf:
                try:
                    os.startfile(self.ultimo_pdf)
                    self._log("PDF abierto automaticamente.")
                except Exception as e:
                    self._log(f"No se pudo abrir el PDF: {e}")
            
            comidas = ['desayuno', 'almuerzo', 'comida', 'cena']
            kcal_real = sum(plan[c].get('kcal_real', 0) for c in comidas if c in plan)
            desv_max = max(plan[c].get('desviacion_pct', 0) for c in comidas if c in plan)
            
            print("\n" + "=" * 60)
            print("  PLAN GENERADO EXITOSAMENTE!")
            print("=" * 60)
            print(f"\n  Cliente: {nombre}")
            print(f"  Objetivo: {objetivo.upper()}")
            print(f"  Kcal objetivo: {cliente.kcal_objetivo:.0f}")
            print(f"  Kcal reales: {kcal_real:.0f}")
            print(f"  Desviacion maxima: {desv_max:.2f}%")
            print(f"\n  PDF guardado en: {ruta_pdf}")
            print("\n" + "=" * 60)
            
        except ValueError as ve:
            self._log(f"Error de validacion: {ve}")
            messagebox.showerror("Error de Validacion", f"Por favor verifica los datos.\nDetalle: {ve}")
        except Exception as e:
            self._log(f"ERROR: {str(e)}")
            messagebox.showerror("Error", f"Ocurrio un error:\n{str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.after(0, self._hide_spinner_on_button)
            self.after(0, lambda: self.btn_procesar.configure(state="normal", text="GENERAR PLAN Y PDF"))

    def _show_spinner_on_button(self):
        try:
            spinner_path = resource_path("assets/spinner_dark.gif")
            if not os.path.exists(spinner_path):
                self.btn_procesar.configure(text="Generando plan...", image=None)
                return
            self.spinner_img = Image.open(spinner_path)
            self.spinner_frames = []
            try:
                while True:
                    self.spinner_frames.append(ImageTk.PhotoImage(self.spinner_img.copy()))
                    self.spinner_img.seek(len(self.spinner_frames))
            except EOFError:
                pass
            self._spinner_frame = 0
            self._spinner_running = True
            self._animate_spinner()
        except Exception:
            self.btn_procesar.configure(text="Generando plan...", image=None)

    def _animate_spinner(self):
        if not getattr(self, '_spinner_running', False):
            return
        frame = self.spinner_frames[self._spinner_frame]
        self.btn_procesar.configure(text="Generando plan...", image=frame, compound="left")
        self._spinner_frame = (self._spinner_frame + 1) % len(self.spinner_frames)
        self.after(60, self._animate_spinner)

    def _hide_spinner_on_button(self):
        self._spinner_running = False
        self.btn_procesar.configure(text="GENERAR PLAN Y PDF", image=None)

    def _abrir_pdf(self):
        if self.ultimo_pdf and os.path.exists(self.ultimo_pdf):
            try:
                os.startfile(self.ultimo_pdf)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el PDF: {e}")
        else:
            messagebox.showwarning("Aviso", "No hay PDF disponible para abrir.")

    def abrir_carpeta_pdf(self):
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        os.startfile(CARPETA_SALIDA)

    def enviar_por_whatsapp(self):
        if not self.ultimo_pdf or not os.path.exists(self.ultimo_pdf):
            messagebox.showerror("Error", "Primero debes generar el plan.")
            return
        telefono = self.entry_telefono.get().strip()
        if not telefono.isdigit():
            messagebox.showerror("Error", "Teléfono inválido.")
            return
        if not telefono.startswith("52"):
            messagebox.showerror("Error", "El número debe iniciar con 52 (México).")
            return
        nombre = self.entry_nombre.get().strip()

        mensaje = f"""
    Hola {nombre} 👋

    Tu plan personalizado de FitnessGym Real Del Valle ya está listo.
    Adjunto encontrarás tu plan alimenticio.
    Cualquier duda puedes consultarla directamente con tu entrenador de piso en recepción.
    FitnessGym Real Del Valle agradece tu preferencia y te espera el próximo mes con tu plan actualizado.
    """

        mensaje_codificado = urllib.parse.quote(mensaje)
        url = f"https://wa.me/{telefono}?text={mensaje_codificado}"
        webbrowser.open(url)
        
        messagebox.showinfo(
            "WhatsApp",
            "WhatsApp Web abierto. Adjunta el PDF manualmente y envía."
        )

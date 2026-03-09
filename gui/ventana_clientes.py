# -*- coding: utf-8 -*-
"""
Ventana de gestión de clientes con historial y seguimiento.

Esta ventana permite:
- Ver lista de todos los clientes registrados
- Buscar clientes por nombre/teléfono
- Ver historial detallado de cada cliente
- Exportar datos a Excel
"""

import os
import re
import csv
from datetime import datetime
from typing import Dict, List

import customtkinter as ctk
from tkinter import messagebox

from src.gestor_bd import GestorBDClientes
from utils.logger import logger
from config.constantes import CARPETA_SALIDA
from gui.widgets_toast import mostrar_toast


class VentanaClientes(ctk.CTkToplevel):
    """Ventana de gestión y seguimiento de clientes."""
    
    # Paleta de colores consistente con la app principal
    COLOR_BG = "#0D0D0D"
    COLOR_CARD = "#1A1A1A"
    COLOR_PRIMARY = "#9B4FB0"
    COLOR_PRIMARY_HOVER = "#B565C6"
    COLOR_SECONDARY = "#D4A84B"
    COLOR_BORDER = "#444444"
    COLOR_TEXT = "#F5F5F5"
    COLOR_TEXT_MUTED = "#B8B8B8"
    COLOR_SUCCESS = "#4CAF50"
    COLOR_INFO = "#2196F3"
    
    def __init__(self, master, gestor_bd: GestorBDClientes):
        super().__init__(master)
        
        self.gestor_bd = gestor_bd
        self.clientes_todos: List[dict] = []
        self.clientes_filtrados: List[dict] = []
        
        self.title("Mis Clientes — Método Base")
        self.geometry("900x700")
        self.configure(fg_color=self.COLOR_BG)
        
        # Hacer la ventana modal y centrada
        self.transient(master)
        self.grab_set()
        
        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"900x700+{x}+{y}")
        
        self._construir_ui()
        self._cargar_clientes()
        
        logger.info("[CLIENTES] Ventana abierta")
        
    def _construir_ui(self) -> None:
        """Construye la interfaz de usuario."""
        # Header con título y búsqueda
        self.header_frame = ctk.CTkFrame(
            self, fg_color="transparent", height=80
        )
        self.header_frame.pack(fill="x", padx=20, pady=20)
        self.header_frame.pack_propagate(False)
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(
            self.header_frame,
            text="🏋️ Clientes Registrados",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        self.lbl_titulo.pack(side="left", anchor="w")
        
        # Campo de búsqueda
        self.search_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.search_frame.pack(side="right", anchor="e")
        
        self.lbl_buscar = ctk.CTkLabel(
            self.search_frame,
            text="🔍 Buscar:",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_buscar.pack(side="left", padx=(0, 8))
        
        self.entry_buscar = ctk.CTkEntry(
            self.search_frame,
            placeholder_text="Nombre o teléfono...",
            width=250,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLOR_CARD,
            border_color=self.COLOR_BORDER,
            text_color=self.COLOR_TEXT
        )
        self.entry_buscar.pack(side="left")
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_clientes)
        
        # Frame principal con scroll
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=self.COLOR_BG,
            scrollbar_button_color=self.COLOR_PRIMARY,
            scrollbar_button_hover_color=self.COLOR_PRIMARY_HOVER
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Footer con estadísticas y botón exportar
        self.footer_frame = ctk.CTkFrame(
            self, fg_color=self.COLOR_CARD, height=60
        )
        self.footer_frame.pack(fill="x", padx=20, pady=(0, 20))
        self.footer_frame.pack_propagate(False)
        
        # Contador de clientes
        self.lbl_total = ctk.CTkLabel(
            self.footer_frame,
            text="Total: 0 clientes activos",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.lbl_total.pack(side="left", padx=15, pady=15)
        
        # Botón exportar CSV
        self.btn_exportar = ctk.CTkButton(
            self.footer_frame,
            text="📊 Exportar CSV",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLOR_SUCCESS,
            hover_color="#43A047",
            text_color="white",
            width=140,
            command=self._exportar_excel
        )
        self.btn_exportar.pack(side="right", padx=15, pady=15)
        
    def _cargar_clientes(self, filtro: str = "") -> None:
        """Carga los clientes desde la BD y los muestra."""
        try:
            if filtro.strip():
                self.clientes_filtrados = self.gestor_bd.buscar_clientes(filtro.strip())
            else:
                self.clientes_todos = self.gestor_bd.obtener_todos_clientes(solo_activos=True)
                self.clientes_filtrados = self.clientes_todos.copy()
            
            self._repoblar_tarjetas()
            
        except Exception as e:
            logger.error("[CLIENTES] Error cargando clientes: %s", e)
            messagebox.showerror("Error", f"Error cargando clientes:\\n{e}")
            
    def _repoblar_tarjetas(self) -> None:
        """Limpia el scroll frame y crea nuevas tarjetas de cliente."""
        # Limpiar tarjetas existentes
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        # Actualizar contador
        total = len(self.clientes_filtrados)
        self.lbl_total.configure(text=f"Total: {total} cliente{'s' if total != 1 else ''}")
        
        if not self.clientes_filtrados:
            # Mensaje cuando no hay resultados
            self.lbl_vacio = ctk.CTkLabel(
                self.scroll_frame,
                text="😔 No se encontraron clientes",
                font=ctk.CTkFont(family="Segoe UI", size=16),
                text_color=self.COLOR_TEXT_MUTED
            )
            self.lbl_vacio.pack(pady=50)
            return
            
        # Crear tarjetas para cada cliente
        for cliente in self.clientes_filtrados:
            self._crear_tarjeta_cliente(self.scroll_frame, cliente)
            
    def _crear_tarjeta_cliente(self, parent, cliente: dict) -> None:
        """Crea una tarjeta visual para un cliente."""
        tarjeta = ctk.CTkFrame(
            parent,
            fg_color=self.COLOR_CARD,
            border_width=1,
            border_color=self.COLOR_BORDER,
            corner_radius=12
        )
        tarjeta.pack(fill="x", pady=8, padx=10)
        
        # Layout interno
        tarjeta.grid_columnconfigure(0, weight=1)
        
        # Fila 1: Nombre y fecha
        fila1 = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila1.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 4))
        fila1.grid_columnconfigure(0, weight=1)
        
        nombre_texto = cliente.get('nombre', 'Sin nombre')
        fecha_registro = cliente.get('fecha_registro', '')
        if fecha_registro:
            try:
                fecha_obj = datetime.fromisoformat(fecha_registro.replace('Z', '+00:00'))
                fecha_texto = fecha_obj.strftime('%d/%m/%Y')
            except:
                fecha_texto = str(fecha_registro)[:10]
        else:
            fecha_texto = 'Sin fecha'
            
        lbl_nombre = ctk.CTkLabel(
            fila1,
            text=f"👤 {nombre_texto}",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=self.COLOR_TEXT,
            anchor="w"
        )
        lbl_nombre.grid(row=0, column=0, sticky="w")
        
        lbl_fecha = ctk.CTkLabel(
            fila1,
            text=f"📅 {fecha_texto}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_MUTED
        )
        lbl_fecha.grid(row=0, column=1, sticky="e")
        
        # Fila 2: Datos físicos y objetivo
        fila2 = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila2.grid(row=1, column=0, sticky="ew", padx=15, pady=2)
        
        peso = cliente.get('peso_kg', 0)
        grasa = cliente.get('grasa_corporal_pct', 0)
        objetivo = cliente.get('objetivo', 'Sin objetivo')
        
        info_texto = f"{peso}kg · {grasa}% grasa · {objetivo.title()}"
        
        lbl_info = ctk.CTkLabel(
            fila2,
            text=info_texto,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=self.COLOR_TEXT_MUTED,
            anchor="w"
        )
        lbl_info.pack(anchor="w")
        
        # Fila 3: Planes y botones
        fila3 = ctk.CTkFrame(tarjeta, fg_color="transparent")
        fila3.grid(row=2, column=0, sticky="ew", padx=15, pady=(2, 12))
        fila3.grid_columnconfigure(0, weight=1)
        
        total_planes = cliente.get('total_planes_generados', 0)
        lbl_planes = ctk.CTkLabel(
            fila3,
            text=f"Planes generados: {total_planes}",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=self.COLOR_TEXT_MUTED,
            anchor="w"
        )
        lbl_planes.grid(row=0, column=0, sticky="w")
        
        # Botones
        botones_frame = ctk.CTkFrame(fila3, fg_color="transparent")
        botones_frame.grid(row=0, column=1, sticky="e")
        
        btn_historial = ctk.CTkButton(
            botones_frame,
            text="Ver Historial",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=90,
            height=28,
            fg_color=self.COLOR_INFO,
            hover_color="#1976D2",
            command=lambda c=cliente: self._ver_historial(c['id_cliente'], c['nombre'])
        )
        btn_historial.pack(side="left", padx=(0, 8))
        
        btn_nuevo_plan = ctk.CTkButton(
            botones_frame,
            text="▶",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            width=30,
            height=28,
            fg_color=self.COLOR_PRIMARY,
            hover_color=self.COLOR_PRIMARY_HOVER,
            command=lambda c=cliente: self._nuevo_plan(c)
        )
        btn_nuevo_plan.pack(side="left")
        
    def _filtrar_clientes(self, event=None) -> None:
        """Filtra clientes según el texto de búsqueda."""
        filtro = self.entry_buscar.get().strip()
        self._cargar_clientes(filtro)
        
    def _ver_historial(self, id_cliente: str, nombre: str) -> None:
        """Abre la ventana de historial para un cliente específico."""
        try:
            VentanaHistorialCliente(self, self.gestor_bd, id_cliente, nombre)
        except Exception as e:
            logger.error("[CLIENTES] Error abriendo historial: %s", e)
            messagebox.showerror("Error", f"Error abriendo historial:\\n{e}")
            
    def _nuevo_plan(self, cliente: dict) -> None:
        """Pre-llena los datos del cliente en la ventana principal."""
        messagebox.showinfo(
            "Función en desarrollo",
            f"Próximamente: pre-llenar datos de {cliente['nombre']} "
            f"en la ventana principal para generar nuevo plan."
        )
        
    def _exportar_excel(self) -> None:
        """Exporta todos los clientes a un archivo CSV."""
        try:
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"clientes_reporte_{fecha}.csv"
            ruta = os.path.join(CARPETA_SALIDA, nombre_archivo)
            
            # Asegurar directorio existe
            os.makedirs(CARPETA_SALIDA, exist_ok=True)
            
            # Headers para CSV
            headers = [
                'ID Cliente', 'Nombre', 'Teléfono', 'Edad', 'Peso (kg)',
                'Estatura (cm)', 'Grasa (%)', 'Nivel Actividad', 'Objetivo',
                'Fecha Registro', 'Último Plan', 'Total Planes'
            ]
            
            # Escribir CSV
            with open(ruta, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                for cliente in self.clientes_todos:
                    # Formatear fechas
                    fecha_reg = cliente.get('fecha_registro', '')
                    if fecha_reg:
                        try:
                            fecha_obj = datetime.fromisoformat(fecha_reg.replace('Z', '+00:00'))
                            fecha_reg_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
                        except:
                            fecha_reg_str = str(fecha_reg)
                    else:
                        fecha_reg_str = ''
                        
                    ultimo_plan = cliente.get('ultimo_plan', '')
                    if ultimo_plan:
                        try:
                            fecha_obj = datetime.fromisoformat(ultimo_plan.replace('Z', '+00:00'))
                            ultimo_plan_str = fecha_obj.strftime('%d/%m/%Y %H:%M')
                        except:
                            ultimo_plan_str = str(ultimo_plan)
                    else:
                        ultimo_plan_str = ''
                    
                    fila = [
                        cliente.get('id_cliente', ''),
                        cliente.get('nombre', ''),
                        cliente.get('telefono', ''),
                        cliente.get('edad', ''),
                        cliente.get('peso_kg', ''),
                        cliente.get('estatura_cm', ''),
                        cliente.get('grasa_corporal_pct', ''),
                        cliente.get('nivel_actividad', ''),
                        cliente.get('objetivo', ''),
                        fecha_reg_str,
                        ultimo_plan_str,
                        cliente.get('total_planes_generados', 0)
                    ]
                    writer.writerow(fila)
            
            logger.info("[CLIENTES] CSV exportado: %s", ruta)
            mostrar_toast(f"✅ CSV exportado: {nombre_archivo}", tipo="success")
            
            # Abrir carpeta
            try:
                from utils.helpers import abrir_carpeta_pdf
                abrir_carpeta_pdf(os.path.dirname(ruta))
            except:
                pass
                
        except Exception as e:
            logger.error("[CLIENTES] Error exportando CSV: %s", e)
            messagebox.showerror("Error", f"Error exportando CSV:\\n{e}")


class VentanaHistorialCliente(ctk.CTkToplevel):
    """Sub-ventana que muestra el historial detallado de un cliente."""
    
    COLOR_BG = "#0D0D0D"
    COLOR_CARD = "#1A1A1A"
    COLOR_PRIMARY = "#9B4FB0"
    COLOR_BORDER = "#444444"
    COLOR_TEXT = "#F5F5F5"
    COLOR_TEXT_MUTED = "#B8B8B8"
    COLOR_SUCCESS = "#4CAF50"
    
    def __init__(self, master, gestor_bd: GestorBDClientes, id_cliente: str, nombre: str):
        super().__init__(master)
        
        self.gestor_bd = gestor_bd
        self.id_cliente = id_cliente
        self.nombre = nombre
        
        self.title(f"Historial: {nombre}")
        self.geometry("600x500")
        self.configure(fg_color=self.COLOR_BG)
        
        # Modal y centrado
        self.transient(master)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"600x500+{x}+{y}")
        
        self._construir_ui()
        self._cargar_historial()
        
    def _construir_ui(self) -> None:
        """Construye la interfaz del historial."""
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=20, pady=(20, 10))
        header.pack_propagate(False)
        
        lbl_titulo = ctk.CTkLabel(
            header,
            text=f"📈 Historial: {self.nombre}",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=self.COLOR_TEXT
        )
        lbl_titulo.pack(anchor="w")
        
        # Tabla de historial
        self.scroll_historial = ctk.CTkScrollableFrame(
            self,
            fg_color=self.COLOR_BG,
            scrollbar_button_color=self.COLOR_PRIMARY
        )
        self.scroll_historial.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Footer con botón exportar individual
        footer = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, height=50)
        footer.pack(fill="x", padx=20, pady=(0, 20))
        footer.pack_propagate(False)
        
        btn_exportar_individual = ctk.CTkButton(
            footer,
            text="📊 Exportar CSV Individual",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=self.COLOR_SUCCESS,
            hover_color="#43A047",
            command=self._exportar_excel_individual
        )
        btn_exportar_individual.pack(side="right", padx=15, pady=10)
        
    def _cargar_historial(self) -> None:
        """Carga y muestra el historial del cliente."""
        try:
            planes = self.gestor_bd.obtener_historial_planes(self.id_cliente)
            
            if not planes:
                lbl_vacio = ctk.CTkLabel(
                    self.scroll_historial,
                    text="📝 Este cliente aún no tiene planes generados",
                    font=ctk.CTkFont(family="Segoe UI", size=14),
                    text_color=self.COLOR_TEXT_MUTED
                )
                lbl_vacio.pack(pady=50)
                return
                
            # Header de tabla
            header_frame = ctk.CTkFrame(
                self.scroll_historial, fg_color=self.COLOR_PRIMARY, height=40
            )
            header_frame.pack(fill="x", pady=(0, 5))
            header_frame.pack_propagate(False)
            
            headers = ["Fecha", "Objetivo", "Kcal", "Peso", "Grasa"]
            header_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
            
            for i, header in enumerate(headers):
                lbl = ctk.CTkLabel(
                    header_frame,
                    text=header,
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color="white"
                )
                lbl.grid(row=0, column=i, padx=10, pady=10)
                
            # Filas de datos
            peso_inicial = None
            for plan in sorted(planes, key=lambda p: p.get('fecha_generacion', ''), reverse=True):
                fecha_gen = plan.get('fecha_generacion', '')
                if fecha_gen:
                    try:
                        fecha_obj = datetime.fromisoformat(fecha_gen.replace('Z', '+00:00'))
                        fecha_str = fecha_obj.strftime('%d/%m/%Y')
                    except:
                        fecha_str = str(fecha_gen)[:10]
                else:
                    fecha_str = 'Sin fecha'
                    
                objetivo = plan.get('objetivo', 'N/A')
                kcal = plan.get('kcal_objetivo', 0)
                peso = plan.get('peso_en_momento', 0)
                grasa = plan.get('grasa_en_momento', 0)
                
                if peso_inicial is None:
                    peso_inicial = peso
                
                # Frame de fila
                fila = ctk.CTkFrame(self.scroll_historial, fg_color=self.COLOR_CARD)
                fila.pack(fill="x", pady=2)
                fila.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
                
                # Datos
                datos = [fecha_str, objetivo.title(), f"{kcal:.0f}", f"{peso}kg", f"{grasa}%"]
                for i, dato in enumerate(datos):
                    lbl = ctk.CTkLabel(
                        fila,
                        text=dato,
                        font=ctk.CTkFont(family="Segoe UI", size=11),
                        text_color=self.COLOR_TEXT
                    )
                    lbl.grid(row=0, column=i, padx=10, pady=8)
                    
            # Resumen de evolución
            if peso_inicial and len(planes) > 1:
                peso_actual = planes[0].get('peso_en_momento', peso_inicial)
                cambio = peso_actual - peso_inicial
                
                resumen = ctk.CTkFrame(
                    self.scroll_historial, fg_color=self.COLOR_SUCCESS if cambio <= 0 else "#FF5722"
                )
                resumen.pack(fill="x", pady=(10, 0))
                
                texto_cambio = f"Evolución: {cambio:+.1f}kg en {len(planes)} planes"
                if cambio <= 0:
                    texto_cambio += " ✅"
                    
                lbl_evolucion = ctk.CTkLabel(
                    resumen,
                    text=texto_cambio,
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color="white"
                )
                lbl_evolucion.pack(pady=10)
                
        except Exception as e:
            logger.error("[HISTORIAL] Error cargando historial: %s", e)
            messagebox.showerror("Error", f"Error cargando historial:\\n{e}")
            
    def _exportar_excel_individual(self) -> None:
        """Exporta el seguimiento individual del cliente usando ExportadorMultiformato."""
        from core.exportador_multi import ExportadorMultiformato
        
        try:
            planes = self.gestor_bd.obtener_historial_planes(self.id_cliente)
            if not planes:
                messagebox.showwarning("Aviso", "Este cliente no tiene planes para exportar")
                return
                
            exportador = ExportadorMultiformato()
            ruta_csv = exportador.exportar_seguimiento_cliente(
                self.id_cliente, self.nombre, planes
            )
            
            mostrar_toast(f"✅ CSV individual exportado", tipo="success")
            
            # Abrir carpeta
            try:
                from utils.helpers import abrir_carpeta_pdf
                abrir_carpeta_pdf(os.path.dirname(ruta_csv))
            except:
                pass
                
        except Exception as e:
            logger.error("[HISTORIAL] Error exportando Excel individual: %s", e)
            messagebox.showerror("Error", f"Error exportando Excel individual:\\n{e}")
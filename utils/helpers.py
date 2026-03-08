"""Funciones utilitarias generales."""
import os
import sys
import json
import glob


def resource_path(relative_path):
    """Resuelve rutas portables para PyInstaller y desarrollo."""
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def abrir_carpeta_pdf():
    """Abre la carpeta de salida de PDFs."""
    from config.constantes import CARPETA_SALIDA
    try:
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA, exist_ok=True)
        os.startfile(CARPETA_SALIDA)
    except Exception as e:
        try:
            from tkinter import messagebox
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la carpeta de PDFs.\n\n{str(e)}"
            )
        except Exception:
            pass


def cargar_plan_anterior_cliente(cliente_id: str, directorio_planes: str = ".") -> dict | None:
    """
    Carga el último plan JSON del cliente para obtener peso_base_mes anterior.
    
    Args:
        cliente_id: ID único del cliente
        directorio_planes: Ruta donde buscar archivos plan_*.json
        
    Returns:
        dict: Último plan JSON encontrado o None si no existe
    """
    try:
        pattern = f"plan_{cliente_id}_*.json"
        archivos = glob.glob(os.path.join(directorio_planes, pattern))
        
        if not archivos:
            return None
        
        archivo_reciente = max(archivos, key=os.path.getctime)
        
        with open(archivo_reciente, 'r', encoding='utf-8') as f:
            plan_anterior = json.load(f)
        
        return plan_anterior
    except Exception:
        return None

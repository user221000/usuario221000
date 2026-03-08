"""Gestor de rotación de alimentos para evitar repeticiones."""

import json
import os
from typing import Set, Dict, List


class GestorRotacionAlimentos:
    """Gestiona rotación de alimentos por cliente para evitar repeticiones."""
    
    def __init__(self, id_cliente: str):
        """Inicializa gestor de rotación."""
        self.id_cliente = id_cliente
        self.historial_alimentos = {
            'proteinas': [],
            'carbs': [],
            'grasas': []
        }
        self.cargar_historial()
    
    def cargar_historial(self) -> None:
        """Carga historial de alimentos usados por este cliente."""
        try:
            archivo_hist = f"registros/{self.id_cliente}_historial.json"
            if os.path.exists(archivo_hist):
                with open(archivo_hist, 'r', encoding='utf-8') as f:
                    datos = json.load(f)
                    self.historial_alimentos = datos
                    print(f"      [OK] Historial cargado ({len(self.historial_alimentos['proteinas'])} planes)")
            else:
                print(f"      [INIT] Primer historial para este cliente")
                self.historial_alimentos = {'proteinas': [], 'carbs': [], 'grasas': []}
        except Exception as e:
            print(f"      [ERROR] Error cargando historial: {e}")
            self.historial_alimentos = {'proteinas': [], 'carbs': [], 'grasas': []}
    
    def obtener_penalizados(self) -> Set[str]:
        """Retorna alimentos que NO deben usarse (ya se usaron en el plan anterior)."""
        penalizados = set()
        
        # Penalizar solo el ÚLTIMO plan (no todos los anteriores)
        if self.historial_alimentos['proteinas']:
            penalizados.update(self.historial_alimentos['proteinas'][-1])
            print(f"      ⚠️ Proteínas penalizadas: {self.historial_alimentos['proteinas'][-1]}")
        
        if self.historial_alimentos['carbs']:
            penalizados.update(self.historial_alimentos['carbs'][-1])
            print(f"      ⚠️ Carbos penalizados: {self.historial_alimentos['carbs'][-1]}")
        
        if self.historial_alimentos['grasas']:
            penalizados.update(self.historial_alimentos['grasas'][-1])
            print(f"      ⚠️ Grasas penalizadas: {self.historial_alimentos['grasas'][-1]}")
        
        return penalizados
    
    def registrar_plan(self, plan: Dict) -> None:
        """Registra alimentos del plan actual en historial."""
        proteinas_plan = set()
        carbs_plan = set()
        grasas_plan = set()
        
        proteinas_posibles = {
            'huevo', 'claras_huevo', 'pechuga_de_pollo',
            'carne_magra_res', 'pescado_blanco', 'salmon',
            'queso_panela', 'yogurt_griego_light', 'proteina_suero'
        }
        carbs_posibles = {
            'arroz_blanco', 'arroz_integral', 'papa', 'camote',
            'avena', 'pan_integral', 'tortilla_maiz', 'frijoles',
            'lentejas', 'banana'
        }
        grasas_posibles = {
            'aceite_de_oliva', 'aguacate', 'nueces',
            'almendras', 'mantequilla_mani'
        }
        
        # Recorrer comidas y extraer alimentos usados
        for comida_data in plan.values():
            for alimento, gramos in comida_data['alimentos'].items():
                if gramos > 0:
                    if alimento in proteinas_posibles:
                        proteinas_plan.add(alimento)
                    elif alimento in carbs_posibles:
                        carbs_plan.add(alimento)
                    elif alimento in grasas_posibles:
                        grasas_plan.add(alimento)
        
        # Guardar en historial
        self.historial_alimentos['proteinas'].append(list(proteinas_plan))
        self.historial_alimentos['carbs'].append(list(carbs_plan))
        self.historial_alimentos['grasas'].append(list(grasas_plan))
        
        print(f"      📝 Plan registrado:")
        print(f"         Proteínas usadas: {list(proteinas_plan)}")
        print(f"         Carbos usados: {list(carbs_plan)}")
        print(f"         Grasas usadas: {list(grasas_plan)}")
        
        # Guardar a archivo
        self.guardar_historial()
    
    def guardar_historial(self) -> None:
        """Guarda historial a archivo JSON."""
        os.makedirs('registros', exist_ok=True)
        
        archivo_hist = f"registros/{self.id_cliente}_historial.json"
        with open(archivo_hist, 'w', encoding='utf-8') as f:
            json.dump(self.historial_alimentos, f, indent=2, ensure_ascii=False)
    
    def es_primer_plan(self) -> bool:
        """Retorna True si es el primer plan del cliente."""
        return (
            len(self.historial_alimentos['proteinas']) == 0 and
            len(self.historial_alimentos['carbs']) == 0 and
            len(self.historial_alimentos['grasas']) == 0
        )
    
    def cantidad_planes(self) -> int:
        """Retorna cantidad total de planes generados."""
        return len(self.historial_alimentos['proteinas'])
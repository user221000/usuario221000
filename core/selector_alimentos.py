"""Selección y rotación determinista de alimentos."""
import random
import hashlib

from config.constantes import LEGUMINOSAS
from src.alimentos_base import CATEGORIAS


def generar_seed(cliente, semana: int = 1, gym_id: str = "default") -> int:
    """
    Genera un seed COMPLETAMENTE DETERMINISTA basado en:
    gym_id, cliente.id_cliente, peso_kg, grasa_corporal_pct, objetivo, semana.
    """
    id_cliente = str(cliente.id_cliente).strip().upper()
    peso = float(cliente.peso_kg)
    grasa = float(cliente.grasa_corporal_pct)
    objetivo = str(cliente.objetivo).lower().strip()
    gym = str(gym_id).strip().lower()
    semana_int = int(semana)
    
    seed_string = f"{gym}:{id_cliente}:{peso}:{grasa}:{objetivo}:semana{semana_int}"
    seed_hash = hashlib.sha256(seed_string.encode('utf-8')).hexdigest()
    seed_int = int(seed_hash[:16], 16)
    
    return seed_int


def generar_seed_bloques(cliente, gym_id: str = "default") -> tuple[int, int]:
    """
    Genera seeds para un bloque de 4 semanas (3 semanas base + 1 semana de ajuste).
    Semanas 1-3: seed_base | Semana 4: seed_variacion
    """
    id_cliente = str(cliente.id_cliente).strip().upper()
    peso = float(cliente.peso_kg)
    grasa = float(cliente.grasa_corporal_pct)
    objetivo = str(cliente.objetivo).lower().strip()
    gym = str(gym_id).strip().lower()
    
    seed_base_string = f"{gym}:{id_cliente}:{peso}:{grasa}:{objetivo}:bloque_base"
    seed_base_hash = hashlib.sha256(seed_base_string.encode('utf-8')).hexdigest()
    seed_base = int(seed_base_hash[:16], 16)
    
    seed_var_string = f"{gym}:{id_cliente}:{peso}:{grasa}:{objetivo}:bloque_variacion"
    seed_var_hash = hashlib.sha256(seed_var_string.encode('utf-8')).hexdigest()
    seed_variacion = int(seed_var_hash[:16], 16)
    
    return seed_base, seed_variacion


def obtener_lista_rotada(lista: list, seed: int, meal_idx: int, plan_numero: int = 1) -> list:
    """Mezcla y rota una lista de forma determinista SIN eliminar alimentos."""
    if not lista:
        return []
    
    combined_seed = seed + (plan_numero * 7919)
    rng = random.Random(combined_seed)
    
    lista_mezclada = lista.copy()
    rng.shuffle(lista_mezclada)
    
    rotated = lista_mezclada[meal_idx:] + lista_mezclada[:meal_idx]
    
    if plan_numero > 1 and len(rotated) > 1:
        offset = (plan_numero - 1) % len(rotated)
        rotated = rotated[offset:] + rotated[:offset]
    
    return rotated


def aplicar_penalizacion_semana(lista: list, seed: int, semana: int,
                                factor_penalizacion: float = 0.8) -> list:
    """Penaliza alimentos en semanas posteriores para variar el plan."""
    if semana <= 1 or len(lista) <= 2:
        return lista
    
    porcentaje_penalizacion = 0.10 * (semana - 1)
    cantidad_penalizar = max(1, int(len(lista) * porcentaje_penalizacion))
    
    rng = random.Random(seed + semana)
    alimentos_penalizar = rng.sample(lista, min(cantidad_penalizar, len(lista)))
    
    lista_penalizada = [a for a in lista if a not in alimentos_penalizar] + alimentos_penalizar
    
    return lista_penalizada


class SelectorAlimentos:
    """Selecciona proteína/carb/grasa con rotación por comida."""
    
    @staticmethod
    def seleccionar_lista(tipo: str, meal_idx: int = 0, alimentos_usados=None, seed: int = None, plan_numero: int = 1) -> list:
        """Retorna lista de alimentos para iteración (rotado de forma DETERMINISTA)."""
        if alimentos_usados is None:
            alimentos_usados = set()
        
        proteinas = ['pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon', 'queso_panela', 'huevo',
                     'claras_huevo', 'yogurt_griego_light', 'proteina_suero']
        carbs = ['arroz_blanco', 'arroz_integral', 'papa', 'camote', 'pan_integral', 'avena', 'tortilla_maiz', 'frijoles', 'banana']
        frutas = ['manzana', 'platano', 'papaya', 'naranja', 'mango', 'melon', 'piña']
        grasas = ['aguacate', 'nueces', 'almendras', 'aceite_de_oliva', 'mantequilla_mani']
        
        # Ajustes por comida
        if meal_idx == 0:  # desayuno
            preferidas = ['huevo', 'claras_huevo', 'proteina_suero']
            otras = [p for p in proteinas if p not in preferidas]
            proteinas = [p for p in preferidas if p in proteinas] + otras
            if not proteinas:
                proteinas = ['huevo', 'claras_huevo', 'proteina_suero']
            carbs = ['avena', 'pan_integral', 'tortilla_maiz', 'banana']
            grasas = ['almendras', 'nueces']
        elif meal_idx == 1:  # almuerzo
            proteinas = [p for p in proteinas if p != 'yogurt_griego_light']
            ligeras = ['queso_panela', 'pescado_blanco', 'pechuga_de_pollo']
            otras = [p for p in proteinas if p not in ligeras]
            proteinas = ligeras + otras
            carbs = [c for c in carbs if c != 'arroz_blanco']
            if 'tortilla_maiz' in carbs:
                carbs = ['tortilla_maiz'] + [c for c in carbs if c != 'tortilla_maiz']
            grasas = ['aguacate', 'nueces', 'mantequilla_mani']
        elif meal_idx == 2:  # comida
            proteinas = [p for p in proteinas if p not in ('huevo', 'claras_huevo')]
            proteinas = [p for p in proteinas if p != 'yogurt_griego_light']
            proteinas = [p for p in proteinas if p != 'queso_panela']
            alta_densidad = ['pechuga_de_pollo', 'salmon', 'carne_magra_res', 'pescado_blanco']
            otras = [p for p in proteinas if p not in alta_densidad]
            proteinas = alta_densidad + otras
            frutas = []
        elif meal_idx == 3:  # cena
            proteinas = [p for p in proteinas if p not in ('huevo', 'claras_huevo')]
            proteinas = [p for p in proteinas if p not in ('salmon', 'carne_magra_res', 'queso_panela', 'yogurt_griego_light')]
            proteinas = [p for p in proteinas if p != 'proteina_suero']
            dense = ['arroz_blanco', 'arroz_integral', 'papa', 'camote']
            other = [c for c in carbs if c not in dense]
            carbs = other + dense
            carbs = [c for c in carbs if c != 'tortilla_maiz']
            grasas = [g for g in grasas if g != 'aguacate']
        
        # Aplicar rotación determinista
        if seed is not None and seed != 0:
            proteinas = obtener_lista_rotada(proteinas, seed, meal_idx, plan_numero)
            carbs = obtener_lista_rotada(carbs, seed, meal_idx, plan_numero)
            frutas = obtener_lista_rotada(frutas, seed, meal_idx, plan_numero)
            grasas = obtener_lista_rotada(grasas, seed, meal_idx, plan_numero)
        else:
            if proteinas:
                proteinas = proteinas[meal_idx:] + proteinas[:meal_idx]
            if carbs:
                carbs = carbs[meal_idx:] + carbs[:meal_idx]
            if frutas:
                frutas = frutas[meal_idx:] + frutas[:meal_idx]
            if grasas:
                grasas = grasas[meal_idx:] + grasas[:meal_idx]
        
        # Penalización intra-plan
        proteinas_nuevas = [p for p in proteinas if p not in alimentos_usados]
        if proteinas_nuevas and len(proteinas_nuevas) >= 1:
            proteinas_penalizadas = [p for p in proteinas if p in alimentos_usados]
            proteinas = proteinas_nuevas + proteinas_penalizadas
        
        carbs_nuevos = [c for c in carbs if c not in alimentos_usados]
        if carbs_nuevos and len(carbs_nuevos) >= 1:
            carbs_penalizados = [c for c in carbs if c in alimentos_usados]
            carbs = carbs_nuevos + carbs_penalizados
        
        frutas_nuevas = [f for f in frutas if f not in alimentos_usados]
        if frutas_nuevas and len(frutas_nuevas) >= 1:
            frutas_penalizadas = [f for f in frutas if f in alimentos_usados]
            frutas = frutas_nuevas + frutas_penalizadas
        
        grasas_nuevas = [g for g in grasas if g not in alimentos_usados]
        if grasas_nuevas and len(grasas_nuevas) >= 1:
            grasas_penalizadas = [g for g in grasas if g in alimentos_usados]
            grasas = grasas_nuevas + grasas_penalizadas
        
        seleccion_map = {
            'proteina': proteinas,
            'carbs': carbs,
            'grasa': grasas,
            'fruta': frutas,
        }
        
        lista = seleccion_map.get(tipo, proteinas)
        return lista if lista else ['pechuga_de_pollo'] if tipo == 'proteina' else []
    
    @staticmethod
    def seleccionar(tipo: str) -> str:
        """Selecciona primer alimento del tipo (deprecated, use seleccionar_lista)."""
        proteinas = ['pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon', 'queso_panela', 'huevo']
        carbs = ['arroz_blanco', 'papa', 'camote', 'pan_integral', 'avena', 'tortilla_maiz', 'frijoles']
        grasas = ['aceite_de_oliva', 'nueces', 'aguacate', 'almendras', 'mantequilla_mani']
        
        seleccion_map = {
            'proteina': proteinas,
            'carbs': carbs,
            'grasa': grasas,
        }
        
        opciones = seleccion_map.get(tipo, proteinas)
        return opciones[0]

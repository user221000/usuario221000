"""
Base de alimentos - Versión simplificada y balanceada (PRODUCCIÓN)
Esta es la fuente única de verdad para todos los alimentos y configuración.
"""

# ============================================================================
# BASE DE ALIMENTOS (proteína/carb/grasa por 100g)
# ============================================================================

ALIMENTOS_BASE = {
    # ============================================================================
    # PROTEÍNAS (9 opciones - máximo 3 por comida para diversidad)
    # ============================================================================
    'pechuga_de_pollo':    {'proteina': 31, 'carbs': 0,   'grasa': 3.6,  'kcal': 165},
    'carne_magra_res':     {'proteina': 26, 'carbs': 0,   'grasa': 10,   'kcal': 217},
    'pescado_blanco':      {'proteina': 22, 'carbs': 0,   'grasa': 2,    'kcal': 105},
    'salmon':              {'proteina': 20, 'carbs': 0,   'grasa': 13,   'kcal': 208},
    'huevo':               {'proteina': 13, 'carbs': 1,   'grasa': 11,   'kcal': 155},
    'claras_huevo':        {'proteina': 11, 'carbs': 0.7, 'grasa': 0.2,  'kcal': 52},
    'queso_panela':        {'proteina': 18, 'carbs': 2,   'grasa': 18,   'kcal': 264},
    'yogurt_griego_light': {'proteina': 10, 'carbs': 4,   'grasa': 0.4,  'kcal': 59},
    'proteina_suero':      {'proteina': 80, 'carbs': 8,   'grasa': 6,    'kcal': 400},

    # ============================================================================
    # CARBOHIDRATOS (7 opciones - máximo 2 densos por comida)
    # ============================================================================
    'arroz_blanco':    {'proteina': 2.7, 'carbs': 28,   'grasa': 0.3,  'kcal': 130},
    'arroz_integral':  {'proteina': 2.6, 'carbs': 23,   'grasa': 1,    'kcal': 111},
    'papa':            {'proteina': 2,   'carbs': 17,   'grasa': 0.1,  'kcal': 77},
    'camote':          {'proteina': 1.6, 'carbs': 20,   'grasa': 0.1,  'kcal': 86},
    'avena':           {'proteina': 11,  'carbs': 66,   'grasa': 7,    'kcal': 389},
    'pan_integral':    {'proteina': 9,   'carbs': 41,   'grasa': 3.5,  'kcal': 247},
    'tortilla_maiz':   {'proteina': 5.7, 'carbs': 44,   'grasa': 2.8,  'kcal': 218},

    # ============================================================================
    # GRASAS (5 opciones - máximo 1 por comida)
    # ============================================================================
    'aceite_de_oliva':   {'proteina': 0,  'carbs': 0,  'grasa': 100, 'kcal': 900},
    'aguacate':          {'proteina': 2,  'carbs': 9,  'grasa': 15,  'kcal': 160},
    'nueces':            {'proteina': 15, 'carbs': 14, 'grasa': 65,  'kcal': 654},
    'almendras':         {'proteina': 21, 'carbs': 22, 'grasa': 49,  'kcal': 579},
    'mantequilla_mani':  {'proteina': 25, 'carbs': 20, 'grasa': 50,  'kcal': 588},

    # ============================================================================
    # VERDURAS (5 opciones - ilimitadas, rotación por comida)
    # ============================================================================
    'brocoli':       {'proteina': 2.8, 'carbs': 7,   'grasa': 0.4, 'kcal': 34},
    'espinaca':      {'proteina': 2.9, 'carbs': 3.6, 'grasa': 0.4, 'kcal': 23},
    'calabacita':    {'proteina': 1.2, 'carbs': 3.1, 'grasa': 0.3, 'kcal': 17},
    'champiñones':   {'proteina': 3.1, 'carbs': 3.3, 'grasa': 0.3, 'kcal': 22},
    'coliflor':      {'proteina': 1.9, 'carbs': 5,   'grasa': 0.3, 'kcal': 25},

    # ============================================================================
    # FRUTAS (7 opciones - solo desayuno y cena, sin repetición en el mismo día)
    # ============================================================================
    'manzana':       {'proteina': 0.3, 'carbs': 14,  'grasa': 0.2, 'kcal': 52},
    'platano':       {'proteina': 1.1, 'carbs': 27,  'grasa': 0.3, 'kcal': 89},
    'banana':        {'proteina': 1.1, 'carbs': 27,  'grasa': 0.3, 'kcal': 89},  # Alias de platano
    'papaya':        {'proteina': 0.6, 'carbs': 12,  'grasa': 0.1, 'kcal': 43},
    'naranja':       {'proteina': 0.7, 'carbs': 12,  'grasa': 0.1, 'kcal': 47},
    'mango':         {'proteina': 0.7, 'carbs': 15,  'grasa': 0.3, 'kcal': 60},
    'melon':         {'proteina': 0.9, 'carbs': 8,   'grasa': 0.2, 'kcal': 34},
    'piña':          {'proteina': 0.5, 'carbs': 13,  'grasa': 0.1, 'kcal': 50},
}

# ============================================================================
# LÍMITES POR COMIDA (gramos) - SIMPLIFICADOS Y REALISTAS
# ============================================================================

LIMITES_ALIMENTOS = {
    # Proteínas magras - máximo 250g
    'pechuga_de_pollo':    250,
    'carne_magra_res':     250,
    'pescado_blanco':      200,    # Máximo 200g
    'salmon':              150,    # Máximo 150g (mínimo 100g manejado en validación)
    'huevo':               200,    # Control especial: máx 2-3 huevos
    'claras_huevo':        250,    # Para cuando se sobrepasa huevo
    'queso_panela':        150,    # Lácteo: menos volumen
    'yogurt_griego_light': 200,    # Lácteo: menos volumen
    'proteina_suero':      40,     # Polvo: porciones pequeñas
    
    # Carbohidratos densos - máximo 250g (casi medio plato)
    'arroz_blanco':        250,
    'arroz_integral':      250,
    'papa':                250,
    'camote':              250,
    'avena':               150,    # Menos (muy denso)
    'pan_integral':        100,    # Menos (muy denso)
    'tortilla_maiz':       150,    # Porción realista: ~6-8 tortillas
    
    # Grasas - muy concentradas, poco volumen
    'aceite_de_oliva':     20,     # ~1 cucharada sopera
    'aguacate':            150,    # ~1 aguacate
    'nueces':              50,     # ~10-12 nueces
    'almendras':           50,     # ~15-20 almendras
    'mantequilla_mani':    40,     # ~2 cucharadas
    
    # Verduras - casi ilimitadas (< 100 kcal por 200g)
    'brocoli':            150,     # Limitado a 150g
    'espinaca':           120,     # Limitado a 120g
    'calabacita':         200,     # Limitado a 200g
    'champiñones':        300,
    'coliflor':           300,
    
    # Frutas - solo desayuno y cena, máximo 200g
    'manzana':            200,     # ≈ 1-2 manzanas medianas
    'platano':            200,     # ≈ 1-2 plátanos medianos
    'banana':             200,     # ≈ 1-2 bananas medianas (alias de platano)
    'papaya':             200,     # ≈ 1 taza
    'naranja':            200,     # ≈ 1-2 naranjas
    'mango':              150,     # ≈ 1 mango mediano
    'melon':              300,     # ≈ 1 taza
    'piña':               200,     # ≈ 1 taza
}

# ============================================================================
# EQUIVALENCIAS PRÁCTICAS (para que el usuario entienda las porciones)
# ============================================================================

EQUIVALENCIAS_PRACTICAS = {
    # Proteínas
    'pechuga_de_pollo':    '≈ 1 pechuga mediana',
    'carne_magra_res':     '≈ 1 bistec mediano',
    'pescado_blanco':      '≈ 1 fillete mediano',
    'salmon':              '≈ 1 fillete de salmón',
    'huevo':               '≈ 2-3 huevos',
    'claras_huevo':        '≈ 8-9 claras',
    'queso_panela':        '≈ 1 porción mediana',
    'yogurt_griego_light': '≈ 1 taza (200ml)',
    'proteina_suero':      '≈ 1 scoop (cucharada)',
    
    # Carbohidratos
    'arroz_blanco':        '≈ 0.5 taza cocida',
    'arroz_integral':      '≈ 0.5 taza cocida',
    'papa':                '≈ 1-2 papas medianas',
    'camote':              '≈ 1 camote mediano',
    'avena':               '≈ 0.3 taza cruda (puñado)',
    'pan_integral':        '≈ 2 rebanadas',
    'tortilla_maiz':       '≈ 6-8 tortillas',
    'banana':              '≈ 1 banana mediana',
    'frijoles':            '≈ 0.5 taza cocida',
    
    # Grasas
    'aceite_de_oliva':     '≈ 1 cucharada',
    'aguacate':            '≈ 0.5 aguacate',
    'nueces':              '≈ 15-20 nueces',
    'almendras':           '≈ 25-30 almendras',
    'mantequilla_mani':    '≈ 2 cucharadas',
    
    # Verduras
    'brocoli':             '≈ 2-3 puños cerrados',
    'espinaca':            '≈ 1-2 platos',
    'calabacita':          '≈ 1 calabacita pequeña',
    'champiñones':         '≈ 1 puñado grande',
    'coliflor':            '≈ 1 taza',
    
    # Frutas
    'manzana':             '≈ 1-2 manzanas medianas',
    'platano':             '≈ 1 plátano mediano',
    'papaya':              '≈ 1 taza',
    'naranja':             '≈ 1-2 naranjas',
    'mango':               '≈ 1 mango mediano',
    'melon':               '≈ 1 taza',
    'piña':                '≈ 1 taza',
}

# ============================================================================
# CATEGORÍAS DE ALIMENTOS (para rotación y selección)
# ============================================================================

CATEGORIAS = {
    'proteina': [
        'pechuga_de_pollo',
        'carne_magra_res',
        'pescado_blanco',
        'salmon',
        'huevo',
        'claras_huevo',
        'queso_panela',
        'yogurt_griego_light',
        'proteina_suero',
    ],
    'carbs': [
        'arroz_blanco',
        'arroz_integral',
        'papa',
        'camote',
        'avena',
        'pan_integral',
        'tortilla_maiz',
    ],
    'grasa': [
        'aceite_de_oliva',
        'aguacate',
        'nueces',
        'almendras',
        'mantequilla_mani',
    ],
    'verdura': [
        'brocoli',
        'espinaca',
        'calabacita',
        'champiñones',
        'coliflor',
    ],
    'fruta': [
        'manzana',
        'platano',
        'papaya',
        'naranja',
        'mango',
        'melon',
        'piña',
    ],
}

# ============================================================================
# REGLAS DE PENALIZACIÓN (Qué NO se puede repetir en el mismo día)
# ============================================================================

REGLAS_PENALIZACION = {
    'huevo': 1,                    # Max 1x día (huevo + claras = grupo)
    'claras_huevo': 1,             # Max 1x día
    'salmon': 1,                   # Max 1x día (muy graso)
    'carne_magra_res': 1,          # Max 1x día (rojo)
    'pechuga_de_pollo': 2,         # Max 2x día (pollo es versátil)
    'pescado_blanco': 1,           # Max 1x día
    'aceite_de_oliva': 1,          # Max 1x día (grasa concentrada)
}

# ============================================================================
# ROTACIONES POR COMIDA (Orden de preferencia)
# ============================================================================

ROTACIONES = {
    'desayuno': {
        'proteina': ['proteina_suero', 'yogurt_griego_light', 'huevo', 'claras_huevo', 'queso_panela'],
        'carbs': ['avena', 'pan_integral', 'tortilla_maiz'],
        'grasa': ['aceite_de_oliva', 'nueces', 'almendras'],
        'verdura': ['brocoli', 'espinaca'],
        'fruta': ['platano', 'manzana', 'papaya', 'naranja', 'mango', 'melon', 'piña'],
    },
    'comida': {
        'proteina': ['pechuga_de_pollo', 'carne_magra_res', 'pescado_blanco', 'salmon'],
        'carbs': ['arroz_blanco', 'arroz_integral', 'papa', 'camote', 'tortilla_maiz'],
        'grasa': ['aguacate', 'nueces', 'mantequilla_mani'],
        'verdura': ['espinaca', 'calabacita', 'champiñones'],
    },
    'cena': {
        'proteina': ['pechuga_de_pollo', 'pescado_blanco', 'claras_huevo', 'queso_panela'],
        'carbs': ['papa', 'camote', 'pan_integral'],
        'grasa': ['nueces', 'almendras'],
        'verdura': ['calabacita', 'coliflor', 'brocoli'],
        'fruta': ['manzana', 'papaya', 'naranja', 'melon', 'piña', 'platano', 'mango'],
    },
}

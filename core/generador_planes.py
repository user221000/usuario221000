"""CAPA 4: Construcción de planes nutricionales completos."""
import os
from datetime import datetime

from config.constantes import (
    PROTEIN_FOODS, FACTORES_ACTIVIDAD, MODO_ESTRICTO,
    LIMITES_DUROS_ALIMENTOS, CARPETA_SALIDA,
    ALIMENTOS_LIMITE_ESTRICTO, MINIMOS_POR_ALIMENTO,
    PROTEINAS_ESTRUCTURALES, PROTEINAS_MIXTAS,
)
from src.alimentos_base import ALIMENTOS_BASE, LIMITES_ALIMENTOS, CATEGORIAS
from src.gestor_rotacion import GestorRotacionAlimentos

from core.modelos import ClienteEvaluacion
from core.motor_nutricional import MotorNutricional, AjusteCaloricoMensual
from core.selector_alimentos import (
    SelectorAlimentos, generar_seed, generar_seed_bloques,
)
from core.estructura_comida import MealStructureContract, ConstructorMealStructure
from core.generador_comidas import (
    DistribuidorComidas, CalculadorGramosNuevo, CalculadorGramos,
    ValidadorEnergia, ReajustadorPlan,
)
from utils.helpers import cargar_plan_anterior_cliente


# ============================================================================
# REDONDEO CLÍNICO PARA DESAYUNO
# ============================================================================

def _aplicar_redondeo_clinico_desayuno(comida_dict: dict) -> dict:
    """
    Aplica redondeo clínico SOLO para desayuno.
    
    Reglas de redondeo:
    - Proteínas: múltiplos de 5g
    - Carbohidratos: múltiplos de 10g
    - Grasas: múltiplos de 5g
    - Vegetales: múltiplos de 10g
    """
    if 'alimentos' not in comida_dict:
        return comida_dict
    
    proteinas_set = {'huevo', 'claras_huevo', 'yogurt_griego_light', 'proteina_suero', 
                     'queso_panela', 'pechuga_de_pollo', 'carne_magra_res', 
                     'pescado_blanco', 'salmon'}
    
    carbs_set = {'arroz_blanco', 'arroz_integral', 'papa', 'camote', 'pan_integral', 
                 'avena', 'tortilla_maiz', 'frijoles', 'banana', 'platano'}
    
    grasas_set = {'aguacate', 'nueces', 'almendras', 'aceite_de_oliva', 'mantequilla_mani'}
    
    vegetales_set = {'brocoli', 'espinaca', 'lechuga_romana', 'pepino', 'tomate',
                     'zanahoria', 'calabaza', 'calabacita', 'col'}
    
    def redondear(valor, multiplo):
        return round(valor / multiplo) * multiplo
    
    alimentos_redondeados = {}
    
    for nombre, gramos in comida_dict['alimentos'].items():
        if nombre in proteinas_set:
            gramos_redondeados = redondear(gramos, 5)
        elif nombre in carbs_set:
            gramos_redondeados = redondear(gramos, 10)
        elif nombre in grasas_set:
            gramos_redondeados = redondear(gramos, 5)
        elif nombre in vegetales_set:
            gramos_redondeados = redondear(gramos, 10)
        else:
            gramos_redondeados = redondear(gramos, 5)
        
        gramos_redondeados = max(0, gramos_redondeados)
        
        if gramos_redondeados > 0:
            alimentos_redondeados[nombre] = gramos_redondeados
    
    comida_dict['alimentos'] = alimentos_redondeados
    
    if comida_dict['alimentos']:
        kcal_real = sum(
            g * ALIMENTOS_BASE.get(n, {}).get('kcal', 0) / 100
            for n, g in comida_dict['alimentos'].items()
        )
        kcal_objetivo = comida_dict.get('kcal_objetivo', 1)
        comida_dict['kcal_real'] = kcal_real
        comida_dict['desviacion_pct'] = abs(kcal_real - kcal_objetivo) / max(kcal_objetivo, 1) * 100
    
    return comida_dict


# ============================================================================
# VALIDACIÓN FINAL: Limites estrictos por alimento
# ============================================================================

def _validar_limites_estrictos_por_plan(plan: dict) -> dict:
    """
    Valida que alimentos con límites estrictos no excedan máximo en plan diario.
    FRIJOLES: Máximo 400g total por plan (máximo ~200g por comida individual).
    """
    frijoles_total = 0.0
    for nombre_comida, comida_data in plan.items():
        if 'alimentos' in comida_data and 'frijoles' in comida_data['alimentos']:
            frijoles_total += comida_data['alimentos']['frijoles']
    
    LIMITE_FRIJOLES_PLAN = 400
    
    if frijoles_total > LIMITE_FRIJOLES_PLAN:
        proporcion = LIMITE_FRIJOLES_PLAN / frijoles_total
        
        for nombre_comida, comida_data in plan.items():
            if 'alimentos' in comida_data and 'frijoles' in comida_data['alimentos']:
                frijoles_actual = comida_data['alimentos']['frijoles']
                frijoles_nuevo = min(frijoles_actual * proporcion, 200)
                
                comida_data['alimentos']['frijoles'] = frijoles_nuevo
                
                kcal_real = 0.0
                for ali_nombre, gramos in comida_data['alimentos'].items():
                    if ali_nombre in ALIMENTOS_BASE:
                        kcal_real += gramos * (ALIMENTOS_BASE[ali_nombre]['kcal'] / 100)
                
                comida_data['kcal_real'] = kcal_real
                comida_data['desviacion_pct'] = abs(kcal_real - comida_data['kcal_objetivo']) / max(comida_data['kcal_objetivo'], 1) * 100
    
    return plan


# ============================================================================
# CONSTRUCTOR DEPRECADO (compatibilidad con tests)
# ============================================================================

class ConstructorPlan:
    """
    DEPRECATED: Usar ConstructorPlanNuevo en su lugar.
    Se mantiene solo para compatibilidad con tests existentes.
    """
    
    @staticmethod
    def _ajustar_carbs_por_densidad(carbs_alimentos: dict, meal_idx: int) -> dict:
        for arroz in ('arroz_blanco', 'arroz_integral'):
            gramos = carbs_alimentos.get(arroz, 0)
            if gramos > 300:
                exceso = gramos - 250
                carbs_alimentos[arroz] = 250
                alternativas = ['papa', 'camote', 'pan_integral', 'frijoles']
                dens_arroz = ALIMENTOS_BASE[arroz]['carbs'] / 100
                for alt in alternativas:
                    if alt == arroz:
                        continue
                    dens_alt = ALIMENTOS_BASE[alt]['carbs'] / 100
                    gramos_alt = exceso * dens_arroz / dens_alt
                    limite = LIMITES_ALIMENTOS.get(alt, 999)
                    if gramos_alt <= limite:
                        carbs_alimentos[alt] = carbs_alimentos.get(alt, 0) + gramos_alt
                        break
        if meal_idx == 2:
            threshold = 150
            for item in ('arroz_blanco', 'arroz_integral', 'papa', 'camote'):
                gramos = carbs_alimentos.get(item, 0)
                if gramos > threshold:
                    extra = gramos - threshold
                    carbs_alimentos[item] = threshold
                    kcal_extra = extra * ALIMENTOS_BASE[item]['kcal'] / 100
                    veg_gramos = kcal_extra / (ALIMENTOS_BASE['brocoli']['kcal'] / 100)
                    carbs_alimentos['brocoli'] = carbs_alimentos.get('brocoli', 0) + veg_gramos
        return carbs_alimentos

    @staticmethod
    def construir(cliente: ClienteEvaluacion, gestor_rotacion=None) -> dict:
        """Construye plan con rotación de alimentos."""
        distribuidor = DistribuidorComidas()
        distribucion = distribuidor.distribuir(
            cliente.kcal_objetivo, cliente.proteina_g, cliente.grasa_g, cliente.carbs_g,
        )
        
        if gestor_rotacion is None:
            gestor_rotacion = GestorRotacionAlimentos(cliente.id_cliente)
        
        plan = {}
        selector = SelectorAlimentos()
        calculador = CalculadorGramos()
        vegetales_bajas = ['brocoli', 'espinaca', 'calabacita', 'champiñones', 'coliflor']
        alimentos_usados_plan = set()
        
        meal_idx = 0
        for nombre_comida, macros_comida in distribucion.items():
            penalizados_hoy = gestor_rotacion.obtener_penalizados()
            
            proteinas_list = selector.seleccionar_lista('proteina', meal_idx, alimentos_usados_plan)
            carbs_list = selector.seleccionar_lista('carbs', meal_idx, alimentos_usados_plan)
            grasas_list = selector.seleccionar_lista('grasa', meal_idx, alimentos_usados_plan)
            
            prot_alimentos = calculador.calcular_iterativo(
                macros_comida['proteina'], 'proteina', proteinas_list, meal_idx, penalizados=penalizados_hoy
            )
            
            if meal_idx == 0 and 'huevo' in prot_alimentos:
                if prot_alimentos['huevo'] > 200:
                    exceso = prot_alimentos['huevo'] - 200
                    prot_alimentos['huevo'] = 200
                    prot_alimentos['claras_huevo'] = prot_alimentos.get('claras_huevo', 0) + exceso
            
            prot_alimentos = calculador.filtrar_menores_a_10g(prot_alimentos, 'proteina')
            
            carbs_alimentos = calculador.calcular_iterativo(
                macros_comida['carbs'], 'carbs', carbs_list, meal_idx, penalizados=penalizados_hoy
            )
            carbs_alimentos = calculador.filtrar_menores_a_10g(carbs_alimentos, 'carbs')
            if len(carbs_alimentos) > 1:
                primer_carb = list(carbs_alimentos.keys())[0]
                carbs_alimentos = {primer_carb: carbs_alimentos[primer_carb]}
            
            grasa_alimentos = calculador.calcular_iterativo(
                macros_comida['grasa'], 'grasa', grasas_list, meal_idx, penalizados=penalizados_hoy
            )
            grasa_alimentos = calculador.filtrar_menores_a_10g(grasa_alimentos, 'grasa')
            
            carbs_alimentos = ConstructorPlan._ajustar_carbs_por_densidad(carbs_alimentos, meal_idx)
            
            comida_dict = {
                'kcal_objetivo': macros_comida['kcal'],
                'macros_objetivo': {
                    'proteina': macros_comida['proteina'],
                    'carbs': macros_comida['carbs'],
                    'grasa': macros_comida['grasa'],
                },
                'alimentos': {},
                'kcal_real': 0,
                'desviacion_pct': 0,
            }
            
            comida_dict['alimentos'].update(prot_alimentos)
            comida_dict['alimentos'].update(carbs_alimentos)
            comida_dict['alimentos'].update(grasa_alimentos)
            
            vegetal_gramos = 120
            if cliente.objetivo.lower() == 'deficit':
                vegetal_gramos = 175
            elif cliente.objetivo.lower() == 'superavit':
                vegetal_gramos = 100
            if meal_idx == 2:
                vegetal_gramos += 50
            
            vegetal = vegetales_bajas[meal_idx % len(vegetales_bajas)]
            comida_dict['alimentos'][vegetal] = vegetal_gramos
            
            comida_dict = ValidadorEnergia.validar_y_ajustar(comida_dict, macros_comida['kcal'], meal_idx=meal_idx)
            
            comida_dict['alimentos'] = {
                nombre: gramos
                for nombre, gramos in comida_dict['alimentos'].items()
                if gramos > 0 and nombre in ALIMENTOS_BASE
            }
            
            alimentos_invalidos = [
                nombre for nombre in comida_dict['alimentos'].keys()
                if nombre not in ALIMENTOS_BASE
            ]
            if alimentos_invalidos:
                print(f"⚠️ Alimentos inválidos removidos: {alimentos_invalidos}")
                comida_dict['alimentos'] = {
                    nombre: gramos
                    for nombre, gramos in comida_dict['alimentos'].items()
                    if nombre in ALIMENTOS_BASE
                }
            
            proteinas_presentes = {
                nombre: gramos for nombre, gramos in comida_dict['alimentos'].items()
                if nombre in CATEGORIAS['proteina'] and gramos >= 80
            }
            
            if not proteinas_presentes:
                lista_prot = selector.seleccionar_lista('proteina', meal_idx)
                prot_encontrada = None
                
                for prot in lista_prot:
                    if comida_dict['alimentos'].get(prot, 0) > 0:
                        prot_encontrada = prot
                        break
                
                if not prot_encontrada:
                    prot_encontrada = lista_prot[0] if lista_prot else 'pechuga_de_pollo'
                
                actual = comida_dict['alimentos'].get(prot_encontrada, 0)
                if actual < 100:
                    delta_g = 100 - actual
                    for carb in ['arroz_blanco', 'arroz_integral', 'papa', 'camote']:
                        if carb in comida_dict['alimentos'] and comida_dict['alimentos'][carb] > delta_g:
                            comida_dict['alimentos'][carb] -= delta_g
                            comida_dict['alimentos'][prot_encontrada] = 100
                            comida_dict = ValidadorEnergia.validar_y_ajustar(comida_dict, macros_comida['kcal'], meal_idx=meal_idx)
                            break
            
            comida_dict['alimentos'] = {
                nombre: gramos
                for nombre, gramos in comida_dict['alimentos'].items()
                if gramos > 0
            }
            
            alimentos_usados_plan.update(comida_dict['alimentos'].keys())
            plan[nombre_comida] = comida_dict
            meal_idx += 1
        
        return plan


# ============================================================================
# #16B NUEVO CONSTRUCTOR: Flujo secuencial (Proteína → Carbs → Grasas)
# ============================================================================

class ConstructorPlanNuevo:
    """
    Nueva arquitectura: Construcción secuencial por macronutriente.
    
    Flujo:
    1. Distribuir macros por comida
    2. Para cada comida:
       a. Asignar PROTEÍNA (ESTRUCTURAL → CONGELADA)
       b. Asignar CARBS
       c. Asignar GRASAS
       d. Insertar VEGETAL BASE
       e. Validación energética (ajusta solo carbs/grasas)
    """
    
    @staticmethod
    def construir(cliente: ClienteEvaluacion, plan_numero: int = 1, directorio_planes: str = ".") -> dict:
        """
        Construye plan nutricional de forma COMPLETAMENTE DETERMINISTA con ROTACIÓN.
        """
        # Generar seeds deterministas con bloque de 4 semanas
        bloque = 1 if plan_numero <= 3 else 2
        seed_base, seed_variacion = generar_seed_bloques(cliente, gym_id="default")
        seed = seed_base if bloque == 1 else seed_variacion
        micro_seed = generar_seed(cliente, semana=plan_numero, gym_id="default")
        bloque_indice = bloque
        
        # Ajuste calórico mensual
        kcal_objetivo_original = cliente.kcal_objetivo
        kcal_objetivo_para_usar = cliente.kcal_objetivo
        ajuste_aplicado = False
        
        plan_anterior = cargar_plan_anterior_cliente(cliente.id_cliente, directorio_planes)
        
        kcal_objetivo_para_usar, ajuste_aplicado = AjusteCaloricoMensual.aplicar_ajuste(
            cliente_id=cliente.id_cliente,
            peso_actual=cliente.peso_kg,
            objetivo=cliente.objetivo,
            kcal_objetivo_base=kcal_objetivo_original,
            plan_anterior=plan_anterior,
            directorio_planes=directorio_planes
        )
        ajuste_desc = 'ajuste -5%' if (ajuste_aplicado and cliente.objetivo == 'deficit') else ('ajuste +5%' if (ajuste_aplicado and cliente.objetivo == 'superavit') else 'sin ajuste')
        print(f"  [AJUSTE] Kcal base {kcal_objetivo_original:.0f} -> final {kcal_objetivo_para_usar:.0f} ({ajuste_desc})")
        
        # Recalcular macros si hubo ajuste
        if ajuste_aplicado:
            macros_finales = MotorNutricional.calcular_macros(cliente.peso_kg, kcal_objetivo_para_usar)
        else:
            macros_finales = {
                'proteina_g': cliente.proteina_g,
                'grasa_g': cliente.grasa_g,
                'carbs_g': cliente.carbs_g,
            }
        
        distribuidor = DistribuidorComidas()
        distribucion = distribuidor.distribuir(
            kcal_objetivo_para_usar,
            macros_finales['proteina_g'],
            macros_finales['grasa_g'],
            macros_finales['carbs_g'],
        )
        
        selector = SelectorAlimentos()
        calculador_nuevo = CalculadorGramosNuevo()
        plan = {}
        alimentos_usados_plan = set()
        
        for meal_idx, (nombre_comida, macros_comida) in enumerate(distribucion.items()):
            alimentos_dict = {}
            
            # FASE 1: PROTEÍNA
            lista_proteinas = selector.seleccionar_lista(
                'proteina', meal_idx, alimentos_usados=alimentos_usados_plan,
                seed=seed, plan_numero=plan_numero
            )
            main_protein = None
            for prot in lista_proteinas:
                if not any(item in PROTEIN_FOODS for item in alimentos_dict):
                    main_protein = prot
                    break
            proteinas_asignadas, kcal_proteina, proteina_congelada = (
                calculador_nuevo.asignar_proteina_estructural(
                    macros_comida['proteina'],
                    [main_protein] if main_protein else lista_proteinas,
                    meal_idx,
                    penalizados=set(),
                    alimentos_usados_plan=alimentos_usados_plan
                )
            )
            if not proteina_congelada:
                print(f"⚠️ ADVERTENCIA: Proteína no congelada en {nombre_comida} (plan #{plan_numero})")
            alimentos_dict.update(proteinas_asignadas)
            alimentos_usados_plan.update(proteinas_asignadas.keys())
            proteina_principal = next(iter(proteinas_asignadas.keys()), None)
            
            # Calcular carbs/grasas aportadas por proteína
            carbs_desde_proteina = 0.0
            grasa_desde_proteina = 0.0
            for ali_nombre in proteinas_asignadas:
                ali_data = ALIMENTOS_BASE.get(ali_nombre, {})
                gramos = proteinas_asignadas[ali_nombre]
                carbs_desde_proteina += gramos * (ali_data.get('carbs', 0) / 100)
                grasa_desde_proteina += gramos * (ali_data.get('grasa', 0) / 100)
            
            # FASE 2: CARBS
            lista_carbs = selector.seleccionar_lista(
                'carbs', meal_idx, alimentos_usados=alimentos_usados_plan,
                seed=seed, plan_numero=plan_numero
            )
            carbs_asignados, kcal_carbs = calculador_nuevo.asignar_carbs(
                macros_comida['carbs'], carbs_desde_proteina,
                lista_carbs, meal_idx, alimentos_usados_plan=alimentos_usados_plan
            )
            alimentos_dict.update(carbs_asignados)
            alimentos_usados_plan.update(carbs_asignados.keys())
            
            # FASE 3: GRASAS
            lista_grasas = selector.seleccionar_lista(
                'grasa', meal_idx, alimentos_usados=alimentos_usados_plan,
                seed=seed, plan_numero=plan_numero
            )
            grasas_asignados, kcal_grasas = calculador_nuevo.asignar_grasas(
                macros_comida['grasa'], grasa_desde_proteina,
                lista_grasas, alimentos_usados_plan=alimentos_usados_plan,
                proteina_principal=proteina_principal
            )
            alimentos_dict.update(grasas_asignados)
            alimentos_usados_plan.update(grasas_asignados.keys())
            
            # FASE 4: VEGETAL BASE
            vegetal = calculador_nuevo.insertar_vegetal_base(meal_idx)
            alimentos_dict.update(vegetal)
            
            # FASE 5: VALIDACIÓN ENERGÉTICA
            alimentos_dict = calculador_nuevo.validar_energetica(
                alimentos_dict, macros_comida['kcal'],
                proteina_congelada=True,
                lista_carbs=lista_carbs, lista_grasas=lista_grasas,
                lista_proteinas=lista_proteinas, macros_comida=macros_comida,
                meal_idx=meal_idx, alimentos_usados_plan=alimentos_usados_plan
            )
            
            # CAPA 3c: ConstructorMealStructure - CONTRATO OBLIGATORIO
            comida_estructurada = ConstructorMealStructure.construir(
                nombre_comida=nombre_comida,
                kcal_objetivo=macros_comida['kcal'],
                macros_objetivo={
                    'proteina': macros_comida['proteina'],
                    'carbs': macros_comida['carbs'],
                    'grasa': macros_comida['grasa'],
                },
                alimentos_dict=alimentos_dict,
                macros_comida=macros_comida
            )
            
            # Redondeo clínico solo para desayuno
            if meal_idx == 0:
                comida_estructurada = _aplicar_redondeo_clinico_desayuno(comida_estructurada)
            
            # Validación energética final
            if comida_estructurada.get('desviacion_pct', 0) > 5:
                comida_estructurada = ValidadorEnergia.validar_y_ajustar(
                    comida_estructurada, macros_comida['kcal'], meal_idx=meal_idx
                )
            
            plan[nombre_comida] = comida_estructurada
        
        # Validar límites estrictos
        plan = _validar_limites_estrictos_por_plan(plan)
        
        # Metadatos para próximo mes
        plan['metadata_mes_anterior'] = {
            'peso_base_mes': cliente.peso_kg,
            'kcal_totales_mes': kcal_objetivo_para_usar,
            'kcal_totales_sin_ajuste': kcal_objetivo_original,
            'ajuste_aplicado': ajuste_aplicado,
            'version_motor': '1.0',
            'seed_base': seed_base,
            'seed_variacion': seed_variacion,
            'objetivo': cliente.objetivo,
            'fecha_plan': datetime.now().isoformat(),
        }
        
        # ENFORCE GLOBAL DE LÍMITES
        FACTOR_MAXIMO = 1.2
        for comida_nombre in ['desayuno', 'almuerzo', 'comida', 'cena']:
            if comida_nombre not in plan or 'alimentos' not in plan[comida_nombre]:
                continue
            
            for ali_nombre, gramos in list(plan[comida_nombre]['alimentos'].items()):
                if ali_nombre not in ALIMENTOS_BASE:
                    continue
                limite_duro = LIMITES_DUROS_ALIMENTOS.get(ali_nombre, 999)
                limite_maximo = limite_duro * FACTOR_MAXIMO
                if gramos > limite_maximo:
                    plan[comida_nombre]['alimentos'][ali_nombre] = limite_maximo
            
            kcal_objetivo = plan[comida_nombre].get('kcal_objetivo', 1)
            kcal_real = sum(
                g * ALIMENTOS_BASE[n]['kcal'] / 100
                for n, g in plan[comida_nombre]['alimentos'].items()
                if n in ALIMENTOS_BASE
            )
            plan[comida_nombre]['kcal_real'] = kcal_real
            plan[comida_nombre]['desviacion_pct'] = abs(kcal_real - kcal_objetivo) / max(kcal_objetivo, 1) * 100
        
        # VALIDACIÓN FINAL: Contrato
        es_valido, errores_contrato = MealStructureContract.validar_plan_completo(plan)
        
        if not es_valido:
            comidas_ok = sum(1 for c in ['desayuno', 'almuerzo', 'comida', 'cena']
                            if c in plan and 'kcal_objetivo' in plan.get(c, {}))
            print(f"\n!ALERTA Plan cumple {comidas_ok}/4 comidas con contrato")
            for error in errores_contrato[:5]:
                print(f"   {error}")
            
            print("\n[REAJUSTE AUTOMATICO] Iniciando ciclo de corrección...")
            plan, plan_corregido, logs_reajuste = ReajustadorPlan.reajustar_plan(plan)
            
            for log in logs_reajuste:
                print(f"   {log}")
            
            if plan_corregido:
                print("\n[OK] Plan CORREGIDO después de reajuste automático")
                es_valido = True
            else:
                es_valido, errores_contrato = MealStructureContract.validar_plan_completo(plan)
                
                if MODO_ESTRICTO and not es_valido:
                    print("\n❌ PLAN INVALIDO - REAJUSTE AUTOMATICO FALLIDO (MODO_ESTRICTO)\n")
                    for e in errores_contrato:
                        print(f"   {e}")
                    raise Exception("Plan invalido por violacion de contrato energetico (>5%) - Reajuste fallido")
        else:
            print(f"\n[OK] Plan cumple contrato arquitectonico completamente")
        
        return plan


# ============================================================================
# DEMO
# ============================================================================

def ejecutar_demo_gym():
    """Demo completa del sistema de generación de planes nutricionales."""
    from core.exportador_salida import GeneradorPDFProfesional
    
    os.makedirs("planes", exist_ok=True)
    os.makedirs("datos", exist_ok=True)
    
    clientes_config = [
        {
            'nombre': 'Cliente Deficit', 'id_cliente': 'DEMO_DEF',
            'edad': 30, 'peso_kg': 80.0, 'estatura_cm': 175,
            'grasa_corporal_pct': 20.0, 'nivel_actividad': 'moderada', 'objetivo': 'deficit',
        },
        {
            'nombre': 'Cliente Mantenimiento', 'id_cliente': 'DEMO_MAN',
            'edad': 28, 'peso_kg': 70.0, 'estatura_cm': 170,
            'grasa_corporal_pct': 18.0, 'nivel_actividad': 'leve', 'objetivo': 'mantenimiento',
        },
        {
            'nombre': 'Cliente Superavit', 'id_cliente': 'DEMO_SUP',
            'edad': 25, 'peso_kg': 75.0, 'estatura_cm': 180,
            'grasa_corporal_pct': 15.0, 'nivel_actividad': 'intensa', 'objetivo': 'superavit',
        },
    ]
    
    resultados = []
    
    for config in clientes_config:
        print("\n" + "=" * 70)
        print(f"PROCESANDO: {config['nombre'].upper()}")
        print("=" * 70)
        
        cliente = ClienteEvaluacion(
            nombre=config['nombre'], id_cliente=config['id_cliente'],
            edad=config['edad'], peso_kg=config['peso_kg'],
            estatura_cm=config['estatura_cm'], grasa_corporal_pct=config['grasa_corporal_pct'],
            nivel_actividad=config['nivel_actividad'], objetivo=config['objetivo'],
        )
        
        cliente.factor_actividad = FACTORES_ACTIVIDAD.get(cliente.nivel_actividad, 1.2)
        print(f"  [1] Cliente creado: {cliente.id_cliente}")
        
        cliente = MotorNutricional.calcular_motor(cliente)
        print(f"  [2] TMB: {cliente.tmb:.0f} | GET: {cliente.get_total:.0f} | Kcal: {cliente.kcal_objetivo:.0f}")
        
        kcal_ajustado, ajuste_aplicado = AjusteCaloricoMensual.aplicar_ajuste(
            cliente_id=cliente.id_cliente, peso_actual=cliente.peso_kg,
            objetivo=cliente.objetivo, kcal_objetivo_base=cliente.kcal_objetivo,
            plan_anterior=None, directorio_planes="planes"
        )
        print(f"  [3] Kcal ajustado: {kcal_ajustado:.0f} | Ajuste: {ajuste_aplicado}")
        
        distribucion = DistribuidorComidas.distribuir(
            cliente.kcal_objetivo, cliente.proteina_g, cliente.grasa_g, cliente.carbs_g
        )
        print(f"  [4] Distribuido: Des {distribucion['desayuno']['kcal']:.0f} | Alm {distribucion['almuerzo']['kcal']:.0f} | Com {distribucion['comida']['kcal']:.0f} | Cen {distribucion['cena']['kcal']:.0f}")
        
        plan = ConstructorPlanNuevo.construir(cliente, plan_numero=1, directorio_planes="planes")
        
        es_valido, errores = MealStructureContract.validar_plan_completo(plan)
        if es_valido:
            print("  [6] Plan VÁLIDO según contrato")
        else:
            print(f"  [6] Plan INVÁLIDO: {errores}")
            if MODO_ESTRICTO:
                raise Exception("Plan invalido por violacion de contrato energetico (>5%)")
        
        if not os.path.exists(CARPETA_SALIDA):
            os.makedirs(CARPETA_SALIDA)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_pdf = f"demo_{cliente.id_cliente}_{timestamp}.pdf"
        ruta_pdf_completa = os.path.join(CARPETA_SALIDA, nombre_pdf)
        
        generador_pdf = GeneradorPDFProfesional(ruta_pdf_completa)
        ruta_pdf = generador_pdf.generar(cliente, plan)
        print(f"  [7] PDF: {ruta_pdf}")
        
        comidas_validas = ['desayuno', 'almuerzo', 'comida', 'cena']
        desviacion_max = max(plan[c].get('desviacion_pct', 0) for c in comidas_validas if c in plan)
        kcal_real = sum(plan[c].get('kcal_real', 0) for c in comidas_validas if c in plan)
        
        resultados.append({
            'id_cliente': cliente.id_cliente, 'kcal_objetivo': cliente.kcal_objetivo,
            'kcal_real': kcal_real, 'desviacion_max': desviacion_max,
            'pdf': ruta_pdf, 'valido': es_valido,
        })
    
    print("\n" + "=" * 70)
    print("RESUMEN DEMO COMPLETA")
    print("=" * 70)
    for r in resultados:
        estado = "OK" if r['valido'] else "ERROR"
        print(f"  [{estado}] {r['id_cliente']}: {r['kcal_objetivo']:.0f} kcal | Desv max: {r['desviacion_max']:.2f}%")
    print("=" * 70 + "\n")
    
    return resultados

"""Generador de PDF para planes nutricionales."""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os
from src.alimentos_base import CATEGORIAS, EQUIVALENCIAS_PRACTICAS

# Nota: HORARIOS_COMIDAS y EXPLICACION_OBJETIVOS se importan en generar() 
# para evitar dependencias circulares en tiempo de importación


class GeneradorPDF:
    """Genera PDF profesional con plan nutricional."""
    
    def __init__(self, nombre_archivo=None):
        """Inicializa generador de PDF."""
        self.nombre_archivo = nombre_archivo or "plan_nutricional.pdf"
        self.styles = getSampleStyleSheet()
        self._crear_estilos_custom()
    
    def _crear_estilos_custom(self):
        """Define estilos personalizados."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloPrincipal',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='Subtitulo',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2e5c8a'),
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        # Normal personalizado
        self.styles.add(ParagraphStyle(
            name='NormalCustom',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))
    
    def generar(self, cliente, plan):
        """
        Genera PDF del plan nutricional.
        
        Args:
            cliente: Instancia de ClienteEvaluacion
            plan: Dict con plan por comida
        
        Returns:
            Ruta del archivo PDF generado
        """
        # Importar dinámicamente para evitar dependencias circulares
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from MVPGYMS import HORARIOS_COMIDAS, EXPLICACION_OBJETIVOS
        
        # Crear documento
        doc = SimpleDocTemplate(
            self.nombre_archivo,
            pagesize=A4,
            rightMargin=1.5*cm,
            leftMargin=1.5*cm,
            topMargin=1.5*cm,
            bottomMargin=1.5*cm
        )
        
        # Contenido
        contenido = []
        
        # 1. Encabezado
        contenido.extend(self._crear_encabezado(cliente))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 2. Objetivo y explicación
        contenido.extend(self._crear_explicacion_objetivo(cliente, EXPLICACION_OBJETIVOS))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 3. Horarios de comidas
        contenido.extend(self._crear_horarios_comidas(HORARIOS_COMIDAS))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 4. Datos del cliente
        contenido.extend(self._crear_datos_cliente(cliente))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 5. Motor Nutricional
        contenido.extend(self._crear_motor_nutricional(cliente))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 6. Macronutrientes
        contenido.extend(self._crear_macronutrientes(cliente))
        contenido.append(Spacer(1, 0.5*cm))
        
        # 7. Plan por comida
        contenido.extend(self._crear_plan_comidas(cliente, plan))
        
        # 6. Notas finales
        contenido.append(Spacer(1, 1*cm))
        contenido.extend(self._crear_notas())
        
        # Generar PDF
        try:
            doc.build(contenido)
            print(f"✅ PDF generado: {self.nombre_archivo}")
            return self.nombre_archivo
        except Exception as e:
            print(f"❌ Error al generar PDF: {e}")
            return None
    
    def _crear_encabezado(self, cliente):
        """Encabezado del documento."""
        contenido = []
        
        titulo = Paragraph(
            "🏋️ MVP GYMS",
            self.styles['TituloPrincipal']
        )
        contenido.append(titulo)
        
        subtitulo = Paragraph(
            f"Plan Nutricional Personalizado - {cliente.id_cliente}",
            self.styles['Subtitulo']
        )
        contenido.append(subtitulo)
        
        fecha = Paragraph(
            f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')} | <b>Cliente:</b> {cliente.nombre}",
            self.styles['NormalCustom']
        )
        contenido.append(fecha)
        
        return contenido
    
    def _crear_explicacion_objetivo(self, cliente, explicacion_objetivos):
        """Explica el objetivo y por qué esos macros."""
        contenido = []
        
        objetivo_lower = cliente.objetivo.lower()
        objetivo_info = explicacion_objetivos.get(objetivo_lower, {})
        
        contenido.append(Paragraph("🎯 Tu Objetivo", self.styles['Subtitulo']))
        
        # Descripción
        desc = Paragraph(
            f"<b>{objetivo_info.get('descripcion', 'Desconocido')}</b>",
            self.styles['NormalCustom']
        )
        contenido.append(desc)
        
        # Tabla de detalles
        objetivo_data = [
            ['Aspecto', 'Detalles'],
            ['Cálculo de calorías', objetivo_info.get('calculo', '')],
            ['Proteína', objetivo_info.get('proteina_razon', '')],
            ['Resultado esperado', objetivo_info.get('resultado_esperado', '')],
            ['Duración recomendada', objetivo_info.get('duracion', '')],
        ]
        
        tabla_objetivo = Table(objetivo_data, colWidths=[4*cm, 11*cm])
        tabla_objetivo.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        contenido.append(tabla_objetivo)
        contenido.append(Spacer(1, 0.3*cm))
        
        # Notas
        notas_text = "<b>📌 Consejos prácticos:</b><br/>"
        for nota in objetivo_info.get('notas', []):
            notas_text += f"• {nota}<br/>"
        
        contenido.append(Paragraph(notas_text, self.styles['NormalCustom']))
        
        return contenido
    
    def _crear_horarios_comidas(self, horarios_comidas):
        """Muestra los horarios recomendados para cada comida."""
        contenido = []
        
        contenido.append(Paragraph("⏰ Horarios de Comidas", self.styles['Subtitulo']))
        
        horarios_data = [['Comida', 'Rango horario', 'Contexto', 'Flexibilidad']]
        
        orden_comidas = ['desayuno', 'almuerzo', 'comida', 'cena']
        for comida in orden_comidas:
            if comida in horarios_comidas:
                info = horarios_comidas[comida]
                horarios_data.append([
                    comida.capitalize(),
                    info['rango'],
                    info['contexto'],
                    info['flexibilidad']
                ])
        
        tabla_horarios = Table(horarios_data, colWidths=[2.5*cm, 3.5*cm, 5*cm, 3.5*cm])
        tabla_horarios.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        contenido.append(tabla_horarios)
        contenido.append(Spacer(1, 0.2*cm))
        
        # Nota de flexibilidad
        nota_flex = Paragraph(
            "<b>💡 Flexibilidad:</b> Estos horarios son guías. Puedes ajustarlos según tu cronograma, "
            "pero intenta mantener ~3-4 horas entre comidas para digestión óptima.",
            self.styles['NormalCustom']
        )
        contenido.append(nota_flex)
        
        return contenido
    
    def _crear_datos_cliente(self, cliente):
        """Tabla con datos del cliente."""
        contenido = []
        
        contenido.append(Paragraph("📋 Datos del Cliente", self.styles['Subtitulo']))
        
        datos = [
            ['Campo', 'Valor'],
            ['Nombre', cliente.nombre],
            ['Edad', f"{cliente.edad} años"],
            ['Peso', f"{cliente.peso_kg} kg"],
            ['Estatura', f"{cliente.estatura_cm} cm"],
            ['Grasa Corporal', f"{cliente.grasa_corporal_pct}%"],
            ['Nivel de Actividad', cliente.nivel_actividad.capitalize()],
            ['Objetivo', cliente.objetivo.capitalize()],
        ]
        
        tabla = Table(datos, colWidths=[5*cm, 10*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        contenido.append(tabla)
        
        return contenido
    
    def _crear_motor_nutricional(self, cliente):
        """Resultados del motor Katch-McArdle."""
        contenido = []
        
        contenido.append(Paragraph("⚙️ Motor Nutricional (Katch-McArdle)", self.styles['Subtitulo']))
        
        motor = [
            ['Métrica', 'Valor'],
            ['Masa Magra', f"{cliente.masa_magra:.2f} kg"],
            ['TMB (Tasa Metabólica Basal)', f"{cliente.tmb:.2f} kcal/día"],
            ['GET (Gasto Energético Total)', f"{cliente.get_total:.2f} kcal/día"],
            ['Kcal Objetivo', f"{cliente.kcal_objetivo:.2f} kcal/día"],
        ]
        
        tabla = Table(motor, colWidths=[8*cm, 7*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        contenido.append(tabla)
        
        return contenido
    
    def _crear_macronutrientes(self, cliente):
        """Tabla de macronutrientes diarios."""
        contenido = []
        
        contenido.append(Paragraph("🥗 Macronutrientes Diarios", self.styles['Subtitulo']))
        
        macros = [
            ['Macronutriente', 'Gramos', 'Kcal', '% Distribución'],
            [
                'Proteína',
                f"{cliente.proteina_g:.1f}g",
                f"{cliente.kcal_proteina:.0f}",
                f"{(cliente.kcal_proteina/cliente.kcal_objetivo*100):.1f}%"
            ],
            [
                'Grasas',
                f"{cliente.grasa_g:.1f}g",
                f"{cliente.kcal_grasa:.0f}",
                f"{(cliente.kcal_grasa/cliente.kcal_objetivo*100):.1f}%"
            ],
            [
                'Carbohidratos',
                f"{cliente.carbs_g:.1f}g",
                f"{cliente.kcal_carbs:.0f}",
                f"{(cliente.kcal_carbs/cliente.kcal_objetivo*100):.1f}%"
            ],
            [
                '<b>TOTAL</b>',
                '<b>-</b>',
                f"<b>{cliente.kcal_objetivo:.0f}</b>",
                '<b>100%</b>'
            ],
        ]
        
        tabla = Table(macros, colWidths=[4*cm, 3*cm, 3*cm, 4*cm])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4788')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('BACKGROUND', (0, 4), (-1, 4), colors.HexColor('#90EE90')),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        contenido.append(tabla)
        
        return contenido
    
    def _crear_plan_comidas(self, cliente, plan):
        """Detalles del plan por comida."""
        contenido = []
        
        contenido.append(PageBreak())
        contenido.append(Paragraph("🍽️ Plan Nutricional por Comida (20/25/30/25)", self.styles['Subtitulo']))
        contenido.append(Spacer(1, 0.3*cm))
        
        # Solo procesar comidas válidas (excluir metadata y otras keys)
        comidas_validas = ['desayuno', 'almuerzo', 'comida', 'cena']
        
        for nombre_comida in comidas_validas:
            if nombre_comida not in plan:
                continue
            comida = plan[nombre_comida]
            
            # Validar que sea un dict con estructura de comida
            if not isinstance(comida, dict) or 'kcal_objetivo' not in comida:
                continue
                
            # Título comida
            titulo_comida = Paragraph(
                f"<b>{nombre_comida.upper()}</b>",
                self.styles['Subtitulo']
            )
            contenido.append(titulo_comida)
            
            # Información energética
            info = f"""
            <b>Objetivo:</b> {comida['kcal_objetivo']:.0f} kcal | 
            <b>Real:</b> {comida.get('kcal_real', 0):.0f} kcal | 
            <b>Desviación:</b> {comida.get('desviacion_pct', 0):.1f}% | 
            <b>Macros:</b> P:{comida.get('macros_objetivo', {}).get('proteina', 0):.0f}g | 
            C:{comida.get('macros_objetivo', {}).get('carbs', 0):.0f}g | 
            F:{comida.get('macros_objetivo', {}).get('grasa', 0):.0f}g
            """
            contenido.append(Paragraph(info, self.styles['NormalCustom']))
            
            # Tabla de alimentos CON TIPO Y EQUIVALENCIA PRÁCTICA
            # ✅ Crear función auxiliar para obtener tipo
            def obtener_tipo_alimento(alimento_nombre):
                """Obtiene el tipo de alimento basándose en CATEGORÍAS."""
                for tipo, alimentos in CATEGORIAS.items():
                    if alimento_nombre in alimentos:
                        return tipo.capitalize()
                return "Otro"
            
            def obtener_equivalencia_practica(alimento_nombre):
                """Obtiene la equivalencia práctica del alimento."""
                return EQUIVALENCIAS_PRACTICAS.get(alimento_nombre, "")
            
            alimentos_data = [['Alimento', 'Tipo', 'Gramos', 'Equivalencia']]
            for alimento, gramos in sorted(comida['alimentos'].items()):
                if gramos > 0:
                    gramos_redondeado = int(round(gramos / 10) * 10)
                    tipo_alimento = obtener_tipo_alimento(alimento)
                    equivalencia = obtener_equivalencia_practica(alimento)
                    alimentos_data.append([
                        alimento.replace('_', ' ').capitalize(), 
                        tipo_alimento,
                        f"{gramos_redondeado}g",
                        equivalencia
                    ])
            
            tabla_alimentos = Table(alimentos_data, colWidths=[6.5*cm, 2.5*cm, 1.8*cm, 4.5*cm])
            tabla_alimentos.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2e5c8a')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7.5),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            contenido.append(tabla_alimentos)
            contenido.append(Spacer(1, 0.5*cm))
        
        return contenido
    
    def _crear_notas(self):
        """Notas finales y recomendaciones."""
        contenido = []
        
        notas = """
        <b>📌 Recomendaciones Importantes:</b><br/>
        • Bebe al menos 2-3 litros de agua al día<br/>
        • Los gramos están redondeados a múltiplos de 10g (usa una balanza de cocina)<br/>
        • Puedes variar los alimentos respetando macros similares<br/>
        • Consulta con un nutricionista si tienes alergias o intolerancias<br/>
        • Revisa tu plan cada 2-4 semanas según progreso<br/>
        <br/>
        <b>⚠️ Nota Legal:</b> Este plan es educativo. Consulta a un profesional de salud antes de cambios importantes en tu dieta.<br/>
        <br/>
        <i>Generado por MVP GYMS - {fecha}</i>
        """
        
        contenido.append(Paragraph(
            notas.format(fecha=datetime.now().strftime('%d/%m/%Y %H:%M')),
            self.styles['NormalCustom']
        ))
        
        return contenido

"""Gestor de base de datos SQLite para clientes."""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List


class GestorClientesBD:
    """Gestor de clientes usando SQLite."""
    
    def __init__(self, db_path: str = "registros/clientes.db"):
        """
        Inicializa gestor de BD.
        
        Args:
            db_path: Ruta a archivo SQLite
        """
        self.db_path = db_path
        self.crear_tablas()
    
    def crear_tablas(self) -> None:
        """Crea tablas si no existen."""
        import os
        os.makedirs('registros', exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de clientes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id_cliente TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL,
                edad INTEGER,
                peso_kg REAL,
                estatura_cm REAL,
                grasa_corporal_pct REAL,
                nivel_actividad TEXT,
                objetivo TEXT,
                kcal_objetivo REAL,
                ultima_actualizacion TEXT
            )
        """)
        
        # Tabla de historial de planes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS historial_planes (
                id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
                id_cliente TEXT NOT NULL,
                numero_plan INTEGER,
                fecha_creacion TEXT NOT NULL,
                pdf_ruta TEXT,
                json_ruta TEXT,
                kcal_real REAL,
                desviacion_pct REAL,
                FOREIGN KEY (id_cliente) REFERENCES clientes (id_cliente)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def cliente_existe(self, id_cliente: str) -> bool:
        """Verifica si cliente existe en BD."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id_cliente FROM clientes WHERE id_cliente = ?", (id_cliente,))
        existe = cursor.fetchone() is not None
        
        conn.close()
        return existe
    
    def crear_cliente(self, cliente_dict: Dict) -> bool:
        """
        Crea nuevo cliente en BD.
        
        Args:
            cliente_dict: Dict con datos del cliente
        
        Returns:
            True si se creó exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO clientes (
                    id_cliente, nombre, fecha_creacion, edad, peso_kg,
                    estatura_cm, grasa_corporal_pct, nivel_actividad,
                    objetivo, kcal_objetivo, ultima_actualizacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_dict['id_cliente'],
                cliente_dict['nombre'],
                cliente_dict['fecha_creacion'],
                cliente_dict['edad'],
                cliente_dict['peso_kg'],
                cliente_dict['estatura_cm'],
                cliente_dict['grasa_corporal_pct'],
                cliente_dict['nivel_actividad'],
                cliente_dict['objetivo'],
                cliente_dict['kcal_objetivo'],
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error al crear cliente en BD: {e}")
            return False
    
    def obtener_cliente(self, id_cliente: str) -> Optional[Dict]:
        """
        Obtiene datos del cliente.
        
        Args:
            id_cliente: ID del cliente
        
        Returns:
            Dict con datos o None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE id_cliente = ?", (id_cliente,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return {
            'id_cliente': row[0],
            'nombre': row[1],
            'fecha_creacion': row[2],
            'edad': row[3],
            'peso_kg': row[4],
            'estatura_cm': row[5],
            'grasa_corporal_pct': row[6],
            'nivel_actividad': row[7],
            'objetivo': row[8],
            'kcal_objetivo': row[9],
            'ultima_actualizacion': row[10]
        }
    
    def buscar_por_nombre(self, nombre: str) -> Optional[Dict]:
        """
        Busca cliente por nombre exacto.
        
        Args:
            nombre: Nombre del cliente
        
        Returns:
            Dict con datos del cliente o None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM clientes WHERE nombre = ?", (nombre,))
        row = cursor.fetchone()
        
        conn.close()
        
        if not row:
            return None
        
        return {
            'id_cliente': row[0],
            'nombre': row[1],
            'fecha_creacion': row[2],
            'edad': row[3],
            'peso_kg': row[4],
            'estatura_cm': row[5],
            'grasa_corporal_pct': row[6],
            'nivel_actividad': row[7],
            'objetivo': row[8],
            'kcal_objetivo': row[9],
            'ultima_actualizacion': row[10]
        }
    
    def registrar_plan(self, id_cliente: str, pdf_ruta: str, json_ruta: str,
                      kcal_real: float, desviacion_pct: float) -> bool:
        """
        Registra un nuevo plan en historial.
        
        Args:
            id_cliente: ID del cliente
            pdf_ruta: Ruta al PDF generado
            json_ruta: Ruta al JSON generado
            kcal_real: Calorías reales del plan
            desviacion_pct: Desviación porcentual
        
        Returns:
            True si se registró exitosamente
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Obtener número de plan actual
            cursor.execute(
                "SELECT MAX(numero_plan) FROM historial_planes WHERE id_cliente = ?",
                (id_cliente,)
            )
            result = cursor.fetchone()
            numero_plan = (result[0] if result[0] else 0) + 1
            
            # Insertar plan
            cursor.execute("""
                INSERT INTO historial_planes (
                    id_cliente, numero_plan, fecha_creacion,
                    pdf_ruta, json_ruta, kcal_real, desviacion_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                id_cliente,
                numero_plan,
                datetime.now().isoformat(),
                pdf_ruta,
                json_ruta,
                kcal_real,
                desviacion_pct
            ))
            
            # Actualizar última_actualizacion del cliente
            cursor.execute(
                "UPDATE clientes SET ultima_actualizacion = ? WHERE id_cliente = ?",
                (datetime.now().isoformat(), id_cliente)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Error al registrar plan: {e}")
            return False
    
    def obtener_historial(self, id_cliente: str) -> List[Dict]:
        """
        Obtiene historial de planes del cliente.
        
        Args:
            id_cliente: ID del cliente
        
        Returns:
            Lista de planes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id_plan, numero_plan, fecha_creacion, pdf_ruta, json_ruta,
                   kcal_real, desviacion_pct
            FROM historial_planes
            WHERE id_cliente = ?
            ORDER BY numero_plan DESC
        """, (id_cliente,))
        
        rows = cursor.fetchall()
        conn.close()
        
        historial = []
        for row in rows:
            historial.append({
                'id_plan': row[0],
                'numero_plan': row[1],
                'fecha': row[2],
                'pdf_ruta': row[3],
                'json_ruta': row[4],
                'kcal_real': row[5],
                'desviacion_pct': row[6]
            })
        
        return historial
    
    def obtener_estadisticas(self, id_cliente: str) -> Dict:
        """Obtiene estadísticas del cliente."""
        historial = self.obtener_historial(id_cliente)
        
        return {
            'total_planes': len(historial),
            'ultimo_plan': historial[0] if historial else None,
            'historial': historial
        }

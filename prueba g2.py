import re
import cantools
import pandas as pd
from collections import defaultdict
import xlsxwriter
import numpy as np
import matplotlib.pyplot as plt
import operator
from typing import List, Dict
from numpy import log, log10, sin, cos, tan, exp, sqrt  
from scipy.io import savemat  

class Señal:

    def __init__(self, ruta_dbc: str):
        try:
            self.db = cantools.database.load_file(ruta_dbc)
            print(f"DBC cargado: {ruta_dbc}")
        except Exception as e:
            print(f"Error al cargar el archivo DBC: {e}")
            raise

        self._imprimir_ids_mensajes()
        # Operaciones aritméticas básicas disponibles
        self.operaciones = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }
        # Precedencia para cada operador
        self.precedencia = {
            '+': 2,
            '-': 2,
            '*': 1,
            '/': 1
        }

    def _imprimir_ids_mensajes(self):
        print("IDs de mensaje definidos en el DBC:")
        for mensaje in self.db.messages:
            print(f"ID: {mensaje.frame_id} ({mensaje.name})")

    def _guardar_en_csv(self, df: pd.DataFrame, csv_final: str):
        """Guardar los datos en formato CSV."""
        df.to_csv(csv_final, index=False)
        print(f"Decodificación completada y guardada en {csv_final}")

    def _guardar_en_mat(self, df: pd.DataFrame, archivo_mat: str):
        """Guardar los datos en formato .mat para MATLAB."""
        datos_mat = {col: df[col].values for col in df.columns}
        savemat(archivo_mat, datos_mat)
        print(f"Datos guardados en {archivo_mat} en formato MATLAB.")

    def _guardar_en_excel(self, df: pd.DataFrame, archivo_excel: str, ruta_grafico: str = None):
        """Guardar los datos en Excel línea por línea e insertar gráfico en una segunda hoja."""
        df_limpio = df.fillna('').replace([np.inf, -np.inf], '')  # Reemplazar NaN e inf por cadena vacía
        workbook = xlsxwriter.Workbook(archivo_excel)
        worksheet = workbook.add_worksheet("Datos")

        # Escribir los datos en la primera hoja
        for col_num, valor in enumerate(df_limpio.columns):
            worksheet.write(0, col_num, valor)

        for fila_num, fila in enumerate(df_limpio.itertuples(index=False), 1):
            worksheet.write_row(fila_num, 0, fila)

        # Insertar el gráfico en la segunda hoja si se proporcionó
        if ruta_grafico:
            worksheet_grafico = workbook.add_worksheet("Gráfico")
            worksheet_grafico.insert_image('B2', ruta_grafico)

        workbook.close()
        print(f"Decodificación completada y guardada en {archivo_excel}")

    def _guardar_en_ascii(self, df: pd.DataFrame, archivo_ascii: str):
        """Guardar los datos en formato ASCII (archivo de texto)."""
        with open(archivo_ascii, 'w') as archivo:
            archivo.write('\t'.join(df.columns) + '\n')
            for _, fila in df.iterrows():
                archivo.write('\t'.join(map(str, fila.values)) + '\n')
        print(f"Datos guardados en {archivo_ascii} en formato ASCII.")

    def _graficar_señales(self, df: pd.DataFrame, señales: list, archivo_grafico: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        plt.figure(figsize=(10, 6))
        for señal in señales:
            if señal in df.columns:
                plt.plot(df['Timestamp'], df[señal], label=señal)
            else:
                print(f"Advertencia: Señal '{señal}' no encontrada en los datos.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Valor de la Señal')
        plt.title('Señales en el Tiempo')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if archivo_grafico:
            plt.savefig(archivo_grafico)
            plt.close()
            print(f"Gráfico guardado en {archivo_grafico}")
        else:
            plt.show()

    def evaluar_expresion(self, expresion: str, df: pd.DataFrame):
        """Evaluar expresiones que contienen operaciones aritméticas básicas entre columnas."""
        expresion = expresion.replace("^", "**")  # Reemplazar potencias para uso en eval

        columnas = re.findall(r'[a-zA-Z_]+', expresion)  # Buscar nombres de columnas

        eval_dict = {col: df[col] for col in columnas if col in df.columns}

        # Incluir funciones matemáticas básicas si es necesario
        funciones_matematicas = {
            'log': log,
            'log10': log10,
            'sin': sin,
            'cos': cos,
            'tan': tan,
            'exp': exp,
            'sqrt': sqrt
        }

        eval_scope = {**eval_dict, **funciones_matematicas}

        try:
            # Evaluar la expresión de forma segura
            resultado = eval(expresion, {"__builtins__": None}, eval_scope)
        except Exception as e:
            print(f"Error al evaluar la expresión: {e}")
            return None

        return resultado

    def procesar_comando_usuario(self, comando_usuario: str, df: pd.DataFrame):
        comando_usuario = comando_usuario.strip()
        
        if comando_usuario.startswith("OP:"):
            expresion = comando_usuario[3:].strip()
            print(f"Evaluando la expresión: {expresion}")
            resultado = self.evaluar_expresion(expresion, df)
            print("Resultado de la Operación:", resultado)
            return resultado
        else:
            print("Comando no válido. Usa 'OP:' al inicio de tu entrada.")

    def agregar_operacion(self, df, nombre_columna: str, resultado):
        """Agregar una nueva columna con el resultado de la operación."""
        df[nombre_columna] = resultado
        return df

    def decodificar_log(self, ruta_log: str, archivo_salida: str, formato_salida: str, señales_a_graficar=None, comando_usuario=None, nombre_columna=None):
        """Decodificar el archivo de log usando el archivo DBC y generar los resultados"""
        patron = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interfaz>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<datos>[0-9A-F]{2,16})'
        
        # Abrir el archivo de log
        try:
            with open(ruta_log, 'r') as archivo:
                log = archivo.read()
        except FileNotFoundError:
            print(f"Error: El archivo de log '{ruta_log}' no se encontró.")
            return
        except Exception as e:
            print(f"Error al abrir el archivo de log: {e}")
            return

        # Compilar el patrón de regex
        regex = re.compile(patron)

        # Diccionario para almacenar los datos decodificados
        decodificado_agrupado = defaultdict(lambda: defaultdict(lambda: None))
        timestamps = set()

        # Realizar los matches y decodificar
        for match in regex.finditer(log):
            timestamp = float(match.group("timestamp"))
            timestamps.add(timestamp)

            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)  # Convertir ID a entero

            try:
                # Convertir datos hexadecimales
                msg_data = bytearray.fromhex(match.group("datos"))
            except ValueError:
                continue

            try:
                # Decodificar mensaje con el DBC
                decodificado = self.db.decode_message(msg_id, msg_data)
                for clave, valor in decodificado.items():
                    if isinstance(valor, (int, float)):
                        decodificado_agrupado[timestamp][clave] = valor
            except Exception as e:
                print(f"Error al decodificar mensaje con ID {msg_id_str} (decimal {msg_id}): {e}")

        # Ordenar timestamps
        timestamps_ordenados = sorted(timestamps)

        # Obtener todas las señales presentes en los logs
        todas_señales = set()
        for datos_decodificados in decodificado_agrupado.values():
            todas_señales.update(datos_decodificados.keys())

        # Crear lista con los datos de señales alineados con los timestamps
        datos = {'Timestamp': timestamps_ordenados}
        for señal in todas_señales:
            datos[señal] = [decodificado_agrupado[timestamp].get(señal, np.nan) for timestamp in timestamps_ordenados]

        # Crear DataFrame de Pandas
        df = pd.DataFrame(datos)

        # Interpolar para cada señal
        for señal in todas_señales:
            df[señal] = df[señal].interpolate(method='linear', limit_direction='both')
        
        # Graficar señales si se proporcionaron
        archivo_grafico = None
        if señales_a_graficar:
            archivo_grafico = "grafico.png"
            self._graficar_señales(df, señales_a_graficar, archivo_grafico)

        if comando_usuario:
            resultado = self.procesar_comando_usuario(comando_usuario, df)
            if resultado is not None:
                df = self.agregar_operacion(df, nombre_columna, resultado)

        # Guardar en el formato solicitado
        if formato_salida.lower() == 'xlsx':
            self._guardar_en_excel(df, archivo_salida, archivo_grafico)
        elif formato_salida.lower() == 'csv':
            self._guardar_en_csv(df, archivo_salida)
        elif formato_salida == 'mat':
            self._guardar_en_mat(df, archivo_salida)
        elif formato_salida == 'ascii':
            self._guardar_en_ascii(df, archivo_salida)
        else:
            print("Formato no soportado")


if __name__ == "__main__":
    try:
        decodificador = Señal("./TER.dbc")
        decodificador.decodificar_log(
            "RUN0.log", "prueba g2", "csv",
            señales_a_graficar=["Barometric_Pressure", "V1", "Heading", "ANGLE"],
            comando_usuario="OP: (Barometric_Pressure + Heading) * 2 / 3", nombre_columna="SOLUCION"
        )
    finally:
        print("Ejecución del decodificador completada.")








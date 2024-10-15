import re
import cantools
import csv
from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt
import pandas as pd
from scipy.io import savemat
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PilImage
import zipfile
from openpyxl import Workbook
import xlsxwriter
import numpy as np

class Signal:
    def __init__(self, dbc_path: str):
        # Cargar el archivo DBC
        try:
            self.db = cantools.database.load_file(dbc_path)
            print(f"Loaded DBC: {dbc_path}")
        except Exception as e:
            print(f"Error loading DBC file: {e}")
            raise

        # Imprimir todos los IDs y sus nombres de mensajes en el DBC
        self._print_message_ids()

    def _print_message_ids(self):
        """Imprime los IDs de los mensajes definidos en el DBC."""
        print("Message IDs defined in the DBC:")
        for message in self.db.messages:
            print(f"ID: {message.frame_id} ({message.name})")
    
    def _write_to_csv(self, df: pd.DataFrame, csv_final: str):
        """Guardar los datos en formato CSV para evitar problemas con archivos Excel grandes."""
        df.to_csv(csv_final, index=False)
        print(f"Decoding completed and saved to {csv_final}")
    
    import zipfile

    from openpyxl import Workbook

    def _write_to_excel_line_by_line(self, df: pd.DataFrame, excel_final: str):
        """Escribir línea por línea en Excel usando xlsxwriter."""

        # Reemplazar NaN e inf por un valor adecuado (por ejemplo, una cadena vacía o un número)
        df_clean = df.fillna('').replace([np.inf, -np.inf], '')

        # Crear el archivo Excel
        workbook = xlsxwriter.Workbook(excel_final)
        worksheet = workbook.add_worksheet("Data")

        # Escribir encabezados
        for col_num, value in enumerate(df_clean.columns):
            worksheet.write(0, col_num, value)

        # Escribir filas una por una (empezando desde la fila 1, después del encabezado)
        for row_num, row in enumerate(df_clean.itertuples(index=False), 1):
            worksheet.write_row(row_num, 0, row)

        # Guardar y cerrar el archivo Excel
        workbook.close()

        print(f"Decoding completed and saved to {excel_final}")


    def decode_log(self, log_path: str, output_file: str, output_format: str):
        """Decodificar el archivo de log usando el archivo DBC y generar los resultados"""
        # Patrón regex para capturar timestamp, interfaz, ID (3 caracteres) y datos
        pattern = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        
        # Abrir el log
        try:
            with open(log_path, 'r') as file:
                log = file.read()
        except FileNotFoundError:
            print(f"Error: El archivo de log '{log_path}' no se encontró.")
            return
        except Exception as e:
            print(f"Error al abrir el archivo de log: {e}")
            return

        # Compilar el patrón de regex
        regex = re.compile(pattern)

        # Diccionario para almacenar los datos decodificados
        grouped_decoded = defaultdict(lambda: defaultdict(lambda: None))
        timestamps = set()

        # Hacer los matches y decodificar
        for match in regex.finditer(log):
            timestamp = float(match.group("timestamp"))
            timestamps.add(timestamp)  # Agregar timestamp a la lista de timestamps

            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)  # Convertir ID a entero

            try:
                # Intentar convertir los datos hexadecimales
                msg_data = bytearray.fromhex(match.group("data"))
            except ValueError:
                #print(f"Error: Los datos '{match.group('data')}' no son válidos como hexadecimal. Se omite este mensaje.")
                continue

            try:
                # Decodificar el mensaje con el DBC
                log_decode = self.db.decode_message(msg_id, msg_data)
                #print(f"Decoded Message ID: {msg_id}, Data: {msg_data.hex()} -> {log_decode}")

                # Agrupar los valores decodificados
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[timestamp][key] = value
                    #else:
                        #print(f"Warning: Signal '{key}' has non-numeric value '{value}' in message ID {msg_id}.")
            #except KeyError:
                #print(f"Warning: Message ID {msg_id_str} (decimal {msg_id}) is not defined in the DBC.")
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        # Ordenar los timestamps
        sorted_timestamps = sorted(timestamps)

        # Obtener todas las señales presentes en los logs
        all_signals = set()
        for decoded_data in grouped_decoded.values():
            all_signals.update(decoded_data.keys())

        # Crear lista con los datos de señales alineados con los timestamps
        data = {'Timestamp': sorted_timestamps}
        for signal in all_signals:
            data[signal] = [grouped_decoded[timestamp].get(signal, None) for timestamp in sorted_timestamps]

        # Crear DataFrame de Pandas
        df = pd.DataFrame(data)

        # Guardar en el formato solicitado
        if output_format == 'xlsx':
           self._write_to_excel_line_by_line(df, output_file)
        elif output_format == 'csv':
            self._write_to_csv(df, output_file)
        else:
            print("Unsupported format")

# Uso del código
if __name__ == "__main__":
    # Asegúrate de usar las rutas correctas para el archivo DBC y el log
    try:
        decoder = Signal("./TER.dbc")
        decoder.decode_log("RUN4.log", "nuevo_pruebaV2.xlsx", "xlsx")
    except Exception as e:
        print(f"Error during execution: {e}")
import pandas as pd
from collections import defaultdict
import cantools
import re
from openpyxl import Workbook

class Signal:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        print(f"Loaded DBC: {dbc_path}")

    def _write_to_xlsx(self, timestamps, signals_dict, xlsx_final: str):
        # Crear un DataFrame vacío con los timestamps como índice y las señales como columnas
        df = pd.DataFrame(index=timestamps)

        # Añadir los valores de las señales al DataFrame
        for signal in signals_dict:
            df[signal] = pd.Series(signals_dict[signal])

        # Convertir todas las columnas a tipo 'object' para poder manejar valores numéricos y vacíos
        df = df.astype(object)

        # Reemplazar NaN con valores vacíos (sin advertencia)
        df.fillna("", inplace=True)

        # Escribir el DataFrame en el archivo Excel
        df.to_excel(xlsx_final, engine='openpyxl', index_label='Timestamp')
        print(f"Decoding and saved to {xlsx_final}")

    def decode_log(self, log_path: str, output_file: str):
        # Expresión regular para extraer los timestamps, ID de mensajes y datos de cada línea del log
        pattern = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        regex = re.compile(pattern)

        # Diccionario para almacenar las señales decodificadas
        signals_dict = defaultdict(dict)  # Almacena {signal_name: {timestamp: value}}
        timestamps_set = set()  # Usamos un set para asegurar que no haya timestamps duplicados

        with open(log_path, 'r') as file:
            log = file.read()

        for match in regex.finditer(log):
            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)
            try:
                msg_data = bytearray.fromhex(match.group("data"))
                timestamp = float(match.group("timestamp"))
                timestamps_set.add(timestamp)  # Añadir timestamp al conjunto
            except ValueError:
                print(f"Error: Los datos '{match.group('data')}' no son válidos como hexadecimal. Se omite este mensaje.")
                continue

            try:
                log_decode = self.db.decode_message(msg_id, msg_data)
                print(f"Decoded Message ID: {msg_id}, Data: {msg_data.hex()} -> {log_decode}")

                # Almacenar los valores decodificados por señal y timestamp
                for signal, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        signals_dict[signal][timestamp] = value
                    else:
                        print(f"Warning: Signal '{signal}' has non-numeric value '{value}' in message ID {msg_id}. Skipping this value.")
            except KeyError:
                print(f"Warning: Message ID {msg_id_str} (decimal {msg_id}) is not defined in the DBC.")
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        # Convertimos el set de timestamps en una lista ordenada
        timestamps = sorted(timestamps_set)

        # Generar el archivo Excel
        self._write_to_xlsx(timestamps, signals_dict, output_file)


if __name__ == "__main__":
    decoder = Signal("./TER.dbc")
    decoder.decode_log("RUN10.log", "RUN10.xlsx")







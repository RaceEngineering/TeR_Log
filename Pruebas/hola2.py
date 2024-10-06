import re
import cantools
import csv
from collections import defaultdict
from typing import List, Dict

class Signal:
    def __init__(self, dbc_path: str):
        # Cargar el archivo DBC
        self.db = cantools.database.load_file(dbc_path)
        print(f"Loaded DBC: {dbc_path}")

    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], csv_final: str):
        # Crear el archivo CSV y escribir los datos
        with open(csv_final, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Escribir encabezados
            writer.writerow(["Signal", "Values"])
            for key, values in grouped_decoded.items():
                writer.writerow([key] + values)

        print(f"Decoding completed and saved to {csv_final}")

    def decode_log(self, log_path: str, csv_final: str):
        # Patrón regex para capturar timestamp, interfaz, ID y datos
        pattern = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3,8})#(?P<data>[0-9A-F]{2,16})'
        
        # Abrir en modo lectura el log
        with open(log_path, 'r') as file:
            log = file.read()
        
        # Compilar regex
        regex = re.compile(pattern)

        # Diccionario de mensajes decodificados
        grouped_decoded = defaultdict(list)

        # Hacer los matches:
        for match in regex.finditer(log):
            msg_id = int(match.group("id"), 16)  # ID del mensaje en hexadecimal
            msg_data = bytearray.fromhex(match.group("data"))  # Convertir datos a bytes

            try:
                # Decodificar con el archivo DBC
                log_decode = self.db.decode_message(msg_id, msg_data)
                print(f"Decoded Message ID: {msg_id}, Data: {msg_data.hex()} -> {log_decode}")

                # Agrupar los valores decodificados
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[key].append(value)
                    else:
                        print(f"Warning: Signal '{key}' has non-numeric value '{value}' in message ID {msg_id}. Skipping this value.")
            except KeyError:
                print(f"Warning: Message with ID {msg_id} is not defined in the DBC.")
            except Exception as e:
                print(f"Error decoding message with ID {msg_id}: {e}")

        self._write_to_csv(grouped_decoded, csv_final)

# Uso del código
if __name__ == "__main__":
    decoder = Signal("./TER.dbc")
    decoder.decode_log("RUN2.log", "decoded_log.csv")

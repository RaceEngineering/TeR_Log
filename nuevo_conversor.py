import re
import cantools
import csv
from collections import defaultdict
from typing import List, Dict

class Signal:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)

    def decode_log(self, log_path:str, csv_final:str):

        pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'
       
        # Abrir en modo lectura el log
        with open(log_path, 'r') as file:
            log = file.read()
       
        # Compilar regex
        regex = re.compile(pattern)

        # Dictionario de mensajes decodificados
        grouped_decoded = defaultdict(list)

        
        # Hacer los matches:
        for match in regex.finditer(log):
            msg = {
                    "data": bytearray.fromhex(match.group(4)),
                    "id": int(match.group(2), 16)
            }
    
            # Decodificar con el TER.dbc
            log_decode = self.db.decode_message(msg["id"], msg["data"])
    
            # Meter todos los values agrupados en cada key
            for key, value in log_decode.items():
                if isinstance(value, (int, float)):
                    grouped_decoded[key].append(value)

        self._write_to_csv(grouped_decoded, csv_final)


    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], csv_final: str):
        # Crear el archivo CSV y escribir los datos
        with open(csv_final, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            for key, values in grouped_decoded.items():
                writer.writerow([key, values])

        print(f"Decoding completed and saved to {csv_final}")

#Uso del codigo
decoder = Signal("./TER.dbc")
decoder.decode_log("RUN0.log", "log_decodificado.csv")


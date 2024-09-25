import re
import cantools
import csv
import pandas as pd
from collections import defaultdict
from typing import Dict, List

class UniversalLogDecoder:
    def __init__(self, dbc_path: str):
        try:
            self.db = cantools.database.load_file(dbc_path)
        except Exception as e:
            print(f"Error loading DBC file: {e}")
            raise

    def decode_log(self, log_path: str, output_format: str, output_file: str):
        pattern = r'(can0\s+)(\d+)\s+\[(\d+)\]\s+([A-F0-9\s]+)'
        
        with open(log_path, 'r') as file:
            log = file.read()

        regex = re.compile(pattern)
        grouped_decoded = defaultdict(list)

        for match in regex.finditer(log):
            msg = {
                "data": bytearray.fromhex(match.group(4).replace(' ', '')),
                "id": int(match.group(2))  # Si el ID es decimal
            }
            try:
                log_decode = self.db.decode_message(msg["id"], msg["data"])
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[key].append(value)
            except Exception as e:
                print(f"Error decoding message ID {msg['id']}: {e}")

        if output_format == 'csv':
            self._write_to_csv(grouped_decoded, output_file)
        elif output_format == 'xlsx':
            self._write_to_excel(grouped_decoded, output_file)
        else:
            print("Unsupported format")

    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], csv_file: str):
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            for key, values in grouped_decoded.items():
                writer.writerow([key] + values)
        print(f"Data saved to {csv_file}")

    def _write_to_excel(self, grouped_decoded: Dict[str, List[float]], excel_file: str):
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in grouped_decoded.items()]))
        df.to_excel(excel_file, index=False)
        print(f"Data saved to {excel_file}")

# Ejemplo de uso
decoder = UniversalLogDecoder("TER.dbc")
decoder.decode_log("RUN0.log", "xlsx", "decoded_log.xlsx")  # Cambia a 'csv' o 'xlsx' según necesites

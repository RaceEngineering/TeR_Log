import re
import cantools
import csv
from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt


class Signal:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
    
    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], csv_final: str):
        # Crear el archivo CSV y escribir los datos
        with open(csv_final, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)

            for key, values in grouped_decoded.items():
                writer.writerow([key, values])

        print(f"Decoding completed and saved to {csv_final}")

    def _plot_signal(self, grouped_decoded: Dict[str, List[float]], signal_name: str, save_path: str = None):
        if signal_name in grouped_decoded:
            plt.figure(figsize=(10, 5))
            plt.plot(grouped_decoded[signal_name], label=signal_name)
            plt.title(f"Signal Plot for {signal_name}")
            plt.xlabel("Time")
            plt.ylabel("Value")
            plt.legend()
            plt.grid(True)
            
            if save_path:
                plt.savefig(save_path)  # Guardar la gráfica en un archivo
                print(f"Plot saved to {save_path}")
                
            plt.show()
        else:
            print(f"Signal {signal_name} not found in the decoded data.")

    def decode_log(self, log_path:str, csv_final:str, signal_to_plot:str=None, plot_save_path: str = None ):

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
        
        if signal_to_plot:
            self._plot_signal(grouped_decoded, signal_to_plot,save_path=plot_save_path)

    

#Uso del codigo
decoder = Signal("./TER.dbc")
decoder.decode_log("RUN0.log", "decoded_log.csv",signal_to_plot="YAW",plot_save_path="YAW_plot.png")
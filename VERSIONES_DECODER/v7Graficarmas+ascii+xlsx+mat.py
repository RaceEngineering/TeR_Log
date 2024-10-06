import re #Libreria para python 
import cantools #Libreria para decodificar los mensajes del CAN
import csv #Libreria para convertir a csv
from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt #Libreria para garficar con python
import pandas as pd #Libreria para convertir en xlsx mas facil pasandolo a un Dataframe
from scipy.io import savemat #Libreria para guardar a un .mat
import operator


class Signal:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        self.grouped_decoded = defaultdict(list)  # Almacenará los valores decodificados

    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], csv_final: str):
        # Crear el archivo CSV y escribir los datos
        with open(csv_final, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            for key, values in grouped_decoded.items():
                writer.writerow([key, values])
        print(f"Decoding completed and saved to {csv_final}")

    def _write_to_xlsx(self, grouped_decoded: Dict[str, List[float]], xlsx_final:str):
         # Convertir el diccionario a un DataFrame de pandas
        df = pd.DataFrame(dict([(k, pd.Series(v)) for k, v in grouped_decoded.items()]))
    
        # Escribir el DataFrame a un archivo Excel
        df.to_excel(xlsx_final, index=False)
        print(f"Decoding completed and saved to {xlsx_final}")
    
    def _write_to_mat(self,grouped_decoded: Dict[str, List[float]], mat_final: str):
        savemat(mat_final,grouped_decoded)
        print(f"Decoding completed and saved to {mat_final}")
    
    def __add__(self, otra_señal):
        # Este método debe ser personalizado para sumar los valores de las señales de dos objetos Signal
        resultado = defaultdict(list)
        for key in self.grouped_decoded:
            if key in otra_señal.grouped_decoded:
                resultado[key] = [a + b for a, b in zip(self.grouped_decoded[key], otra_señal.grouped_decoded[key])]
            else:
                resultado[key] = self.grouped_decoded[key]
        return resultado
    
    def sumar_señales(self, nombres_señales: List[str]) -> float:
        """Función que suma los valores de las señales especificadas."""
        total = 0
        for nombre in nombres_señales:
            if nombre in self.grouped_decoded:
                total += sum(self.grouped_decoded[nombre])
            else:
                print(f"Señal {nombre} no encontrada en los datos decodificados.")
        return total
    
    def _write_to_ascii(self, grouped_decoded: Dict[str, List[float]], ascii_final: str):
        # Crear el archivo ASCII y escribir los datos en un formato de tabla
        with open(ascii_final, mode='w') as ascii_file:
            # Obtener las señales
            signals = grouped_decoded.keys()
            # Escribir el encabezado
            ascii_file.write("\t".join(signals) + "\n")
        
            # Encontrar el número máximo de valores
            max_len = max(len(values) for values in grouped_decoded.values())
            # Escribir los valores de las señales
            for i in range(max_len):
                row = []
                for signal in signals:
                    # Si no hay suficiente valor para esa señal, escribir un valor vacío o 0
                    value = grouped_decoded[signal][i] if i < len(grouped_decoded[signal]) else ""
                    row.append(str(value))
                ascii_file.write("\t".join(row) + "\n")
        print(f"Decoding completed and saved to {ascii_final}")

    def _plot_signals(self, grouped_decoded: Dict[str, List[float]], signal_names: List[str], save_path: str = None):
        plt.figure(figsize=(10, 5))

        for signal_name in signal_names:
            if signal_name in grouped_decoded:
                plt.plot(grouped_decoded[signal_name], label=signal_name)
            else:
                print(f"Signal {signal_name} not found in the decoded data.")
        
        plt.title("Signals Plot")
        plt.xlabel("Sample Number")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)  # Guardar la gráfica en un archivo
            print(f"Plot saved to {save_path}")
        
        plt.show()  # Mostrar la gráfica en pantalla

    def decode_log(self, log_path: str, output_file: str, output_format: str, signals_to_plot: List[str] = None, plot_save_path: str = None):
        pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'
       
        # Abrir en modo lectura el log
        with open(log_path, 'r') as file:
            log = file.read()
       
        # Compilar regex
        regex = re.compile(pattern)

        # Limpiar el diccionario de mensajes decodificados
        self.grouped_decoded.clear()

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
                    self.grouped_decoded[key].append(value)
       
        # Das opción a que elijan formato y llamas a la función específica
        if output_format == 'csv':
            self._write_to_csv(self.grouped_decoded, output_file)
        elif output_format == 'ascii':
            self._write_to_ascii(self.grouped_decoded, output_file)
        elif output_format == 'xlsx':
            self._write_to_xlsx(self.grouped_decoded, output_file)
        elif output_format == 'mat':
            self._write_to_mat(self.grouped_decoded, output_file)
        else:
            print("Unsupported format")
        
        # Graficar las señales si se especifican
        if signals_to_plot:
            self._plot_signals(self.grouped_decoded, signals_to_plot, save_path=plot_save_path)


decoder = Signal("./TER.dbc")
decoder.decode_log("RUN0.log", "decoded_log.mat", "mat")

# Sumar señales específicas
resultado_suma = decoder.sumar_señales(["PITCH", "ROLL"])
print(f"Resultado de la suma de PITCH y ROLL: {resultado_suma}")

#Operadores 


"""from sympy import symbols
# Definir las incógnitas
x, y = symbols('x y')
# Suma de dos incógnitas
resultado_Suma = x + y
print(f"La suma simbólica es: {resultado_Suma}")

# Asignar valores a las incógnitas y evaluar
def resultadosubs(x,y):
    resultado_Suma = x + y
resultado_evaluado = resultadosubs({x: 5, y: 3})
print(f"La suma de 5 y 3 es: {resultado_evaluado}")
"""


import re
import cantools
import pandas as pd
from collections import defaultdict
import xlsxwriter
import numpy as np
import matplotlib.pyplot as plt  # Importar matplotlib para graficar

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
    
    def _write_to_excel_line_by_line(self, df: pd.DataFrame, excel_final: str):
        """Escribir línea por línea en Excel usando xlsxwriter."""
        df_clean = df.fillna('').replace([np.inf, -np.inf], '')  # Reemplazar NaN e inf por cadena vacía
        workbook = xlsxwriter.Workbook(excel_final)
        worksheet = workbook.add_worksheet("Data")

        for col_num, value in enumerate(df_clean.columns):
            worksheet.write(0, col_num, value)

        for row_num, row in enumerate(df_clean.itertuples(index=False), 1):
            worksheet.write_row(row_num, 0, row)
        
        workbook.close()

        print(f"Decoding completed and saved to {excel_final}")

    def _plot_signals(self, df: pd.DataFrame, signals: list):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Signal Value')
        plt.title('Signals Over Time')
        plt.legend()
        plt.grid(True)
        plt.show()

    def decode_log(self, log_path: str, output_file: str, output_format: str, signals_to_plot=None):
        """Decodificar el archivo de log usando el archivo DBC y generar los resultados"""
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
                continue

            try:
                # Decodificar el mensaje con el DBC
                log_decode = self.db.decode_message(msg_id, msg_data)

                # Agrupar los valores decodificados
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[timestamp][key] = value
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
            data[signal] = [grouped_decoded[timestamp].get(signal, np.nan) for timestamp in sorted_timestamps]

        # Crear DataFrame de Pandas
        df = pd.DataFrame(data)

        # Interpolar para cada señal
        for signal in all_signals:
            df[signal] = df[signal].interpolate(method='linear', limit_direction='both')

        # Guardar en el formato solicitado
        if output_format.lower() == 'xlsx':
            self._write_to_excel_line_by_line(df, output_file)
        elif output_format.lower() == 'csv':
            self._write_to_csv(df, output_file)
        else:
            print("Unsupported format")

        # Graficar las señales si se proporcionaron
        if signals_to_plot:
            self._plot_signals(df, signals_to_plot)


# Uso del código
if __name__ == "__main__":
    try:
        decoder = Signal("./TER.dbc")
        # Decodificar y guardar los datos
        decoder.decode_log("RUN4.log", "RUN4_timestamps_interpolados.xlsx", "xlsx", signals_to_plot=["rrRPM","rlRPM","APPS_AV","ANGLE"])  # Cambia Signal1, Signal2 por los nombres reales de las señales
    except Exception as e:
        print(f"Error during execution: {e}")

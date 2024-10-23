import re
import cantools
import pandas as pd
from collections import defaultdict
import xlsxwriter
import numpy as np
import matplotlib.pyplot as plt
import operator
from scipy.io import savemat
from scipy.integrate import cumulative_trapezoid  # Importación corregida
from numpy import gradient  # Para derivación
from typing import List, Dict

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

        # Operaciones básicas
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '**': operator.pow,
        }

    def _print_message_ids(self):
        """Imprime los IDs de los mensajes definidos en el DBC."""
        print("Message IDs defined in the DBC:")
        for message in self.db.messages:
            print(f"ID: {message.frame_id} ({message.name})")

    def evaluate_expression(self, df: pd.DataFrame, expression: str, result_name: str):
        """
        Evalúa una expresión matemática en el contexto del DataFrame y añade el resultado como una nueva columna.
        :param df: El DataFrame de señales.
        :param expression: La expresión a evaluar.
        :param result_name: El nombre de la columna resultante.
        """
        # Asegurarse de que las variables en la expresión sean columnas válidas del DataFrame
        try:
            result = eval(expression, {"__builtins__": None}, df)
            df[result_name] = result
            print(f"Operación '{expression}' evaluada correctamente. Resultado añadido como '{result_name}'.")
        except Exception as e:
            print(f"Error evaluando la expresión '{expression}': {e}")

    def add_derived_signal(self, df: pd.DataFrame, signal: str, result_name: str):
        """
        Deriva la señal dada y añade el resultado como una nueva columna.
        :param df: El DataFrame de señales.
        :param signal: El nombre de la señal a derivar.
        :param result_name: El nombre de la columna de la señal derivada.
        """
        try:
            df[result_name] = np.gradient(df[signal], df['Timestamp'])
            print(f"Derivada de '{signal}' añadida como '{result_name}'.")
        except Exception as e:
            print(f"Error calculando la derivada de '{signal}': {e}")

    def add_integrated_signal(self, df: pd.DataFrame, signal: str, result_name: str):
        """
        Integra la señal dada y añade el resultado como una nueva columna.
        :param df: El DataFrame de señales.
        :param signal: El nombre de la señal a integrar.
        :param result_name: El nombre de la columna de la señal integrada.
        """
        try:
            # Usar cumulative_trapezoid en lugar de cumtrapz
            df[result_name] = cumulative_trapezoid(df[signal], df['Timestamp'], initial=0)
            print(f"Integral de '{signal}' añadida como '{result_name}'.")
        except Exception as e:
            print(f"Error calculando la integral de '{signal}': {e}")

    def _write_to_csv(self, df: pd.DataFrame, csv_final: str):
        """Guardar los datos en formato CSV para evitar problemas con archivos Excel grandes."""
        df.to_csv(csv_final, index=False)
        print(f"Decoding completed and saved to {csv_final}")
    
    def _write_to_mat(self, df: pd.DataFrame, mat_file: str):
        """Guardar los datos en formato .mat para MATLAB."""
        mat_data = {col: df[col].values for col in df.columns}
        savemat(mat_file, mat_data)
        print(f"Data saved to {mat_file} in MATLAB format.")
    
    def _write_to_excel_line_by_line(self, df: pd.DataFrame, excel_final: str, plot_path: str = None):
        """Escribir línea por línea en Excel usando xlsxwriter e insertar gráfico en una segunda hoja."""
        df_clean = df.fillna('').replace([np.inf, -np.inf], '')  # Reemplazar NaN e inf por cadena vacía
        workbook = xlsxwriter.Workbook(excel_final)
        worksheet = workbook.add_worksheet("Data")

        # Escribir datos en la primera hoja
        for col_num, value in enumerate(df_clean.columns):
            worksheet.write(0, col_num, value)

        for row_num, row in enumerate(df_clean.itertuples(index=False), 1):
            worksheet.write_row(row_num, 0, row)
        
        # Insertar la gráfica en la segunda hoja si se proporcionó el gráfico
        if plot_path:
            worksheet_plot = workbook.add_worksheet("Plot")
            worksheet_plot.insert_image('B2', plot_path)  # Insertar la imagen en la celda B2 de la segunda hoja

        workbook.close()

        print(f"Decoding completed and saved to {excel_final}")
    
    def _write_to_ascii(self, df: pd.DataFrame, ascii_file: str):
        """Guardar los datos en formato ASCII (archivo de texto)."""
        with open(ascii_file, 'w') as file:
            # Escribir los encabezados de las columnas
            file.write('\t'.join(df.columns) + '\n')
            # Escribir los datos fila por fila
            for _, row in df.iterrows():
                file.write('\t'.join(map(str, row.values)) + '\n')

        print(f"Data saved to {ascii_file} in ASCII format.")

    def _plot_signals(self, df: pd.DataFrame, signals: list, output_plot: str = None):
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
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
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
        
        # Graficar las señales si se proporcionaron
        plot_file = None
        if signals_to_plot:
            plot_file = "plot.png"
            self._plot_signals(df, signals_to_plot, plot_file)

        # Guardar en el formato solicitado
        if output_format.lower() == 'xlsx':
            self._write_to_excel_line_by_line(df, output_file, plot_file)
        elif output_format.lower() == 'csv':
            self._write_to_csv(df, output_file)
        elif output_format == 'mat':
            self._write_to_mat(df, output_file)
        elif output_format == 'ascii':
            self._write_to_ascii(df,output_file)
        else:
            print("Unsupported format")
        
        return df  # <-- Devuelve el DataFrame

# Uso del código
if __name__ == "__main__":
    try:
        # Cargar el DBC y decodificar el log
        decoder = Signal("./TER.dbc")
        df = decoder.decode_log("RUN4.log", "operadores.xlsx", "xlsx", signals_to_plot=["rrRPM", "rlRPM", "APPS_AV", "ANGLE"])

        # Calcular la derivada de la señal APPS_AV (posiciones del acelerador)
        decoder.add_derived_signal(df, 'APPS_AV', 'APPS_AV_deriv')

        # Calcular la integral de la señal rrRPM (velocidad angular de la rueda trasera derecha)
        decoder.add_integrated_signal(df, 'rrRPM', 'rrRPM_integrated')

        # Sumar las velocidades de las ruedas traseras (rrRPM + rlRPM)
        expression = "df['rrRPM'] + df['rlRPM']"
        decoder.evaluate_expression(df, expression, 'rear_wheels_rpm_sum')

        # Mostrar las primeras filas del DataFrame para verificar los cálculos
        print(df.head())

    except Exception as e:
        print(f"Error during execution: {e}")
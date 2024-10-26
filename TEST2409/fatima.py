import re

import cantools

import pandas as pd

from collections import defaultdict

import xlsxwriter

import numpy as np

import matplotlib.pyplot as plt

import operator

from scipy.io import savemat

from scipy.integrate import cumulative_trapezoid 

from typing import List, Dict

from numpy import log, log10, sin, cos, tan, exp, sqrt  



class Signal:

    def __init__(self, dbc_path: str):

        try:

            self.db = cantools.database.load_file(dbc_path)

            print(f"Loaded DBC: {dbc_path}")

        except Exception as e:

            print(f"Error loading DBC file: {e}")

            raise



        self._print_message_ids()



        self.operations = {

            '+': operator.add,

            '-': operator.sub,

            '*': operator.mul,

            '/': operator.truediv

        }



        self.precedence = {

            '+': 2,

            '-': 2,

            '*': 1,

            '/': 1

        }


    def _print_message_ids(self):

        print("Message IDs defined in the DBC:")

        for message in self.db.messages:

            print(f"ID: {message.frame_id} ({message.name})")
    
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

    def parse_expression(self, expression: str, df: pd.DataFrame):
        """
        Supports math functions like log, sin, cos, etc.
        """
        expression = expression.replace("^", "**")  

        columns = re.findall(r'[a-zA-Z_]+', expression)  

        eval_dict = {col: df[col] for col in columns if col in df.columns}

        math_functions = {

            'log': log,        

            'log10': log10,    

            'sin': sin,

            'cos': cos,

            'tan': tan,

            'exp': exp,

            'sqrt': sqrt

        }

        eval_scope = {**eval_dict, **math_functions}

        return eval(expression, eval_scope)

    def integrate(self, expression: str, df: pd.DataFrame):
        parsed_signal = self.parse_expression(expression, df)
        integrated_signal = cumulative_trapezoid(parsed_signal, df['Timestamp'], initial=0)
        return integrated_signal

    def derivatives(self, expression: str, df: pd.DataFrame):
        parsed_signal = self.parse_expression(expression, df)
        derivative_signal = np.gradient(parsed_signal, df['Timestamp'])
        return derivative_signal

    def process_user_command(self, user_input: str, df: pd.DataFrame):
        user_input = user_input.strip()
        
        if user_input.startswith("INT:"):

            expression = user_input[4:].strip()
            print(f"Integrating the expression: {expression}")
            result = self.integrate(expression, df)
            print("Integration Result:", result)
            return result

        elif user_input.startswith("DER:"):
            expression = user_input[4:].strip()
            print(f"Deriving the expression: {expression}")
            result = self.derivatives(expression, df)
            print("Derivative Result:", result)
            return result
        else:

            print("Invalid command. Use 'INT:' or 'DER:' at the start of your input.")
    
    def add_operation(self, df, operation_result: str, result):
        """
        Agrega una nueva columna de resultado basada en la expresión dada,
        respetando la precedencia de operadores.
        """
        df[operation_result] = result  # Añadir el resultado con un nuevo nombre
        return df
        
    def decode_log(self, log_path: str, output_file: str, output_format: str, signals_to_plot=None, user_input=None, operation_result=None):
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
        
        if user_input:
            result=self.process_user_command(user_input,df)
            if result is not None:
                df = self.add_operation(df,operation_result,result)  #CAMBIARRR

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


if __name__ == "__main__":

    try:

        decoder = Signal("./TER.dbc")
        decoder.decode_log("RUN4.log", "prueba_fatima.csv", "xlsx", signals_to_plot=["rrRPM","rlRPM","APPS_AV","ANGLE"], user_input="INT: log(PITCH^2 + YAW^2)",operation_result="ENERGY")  # Cambia Signal1, Signal2 por los nombres reales de las señales


    except Exception as e:

        print(f"Error during execution: {e}")


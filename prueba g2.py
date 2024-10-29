import re
import cantools
import pandas as pd
from collections import defaultdict 
import xlsxwriter
import numpy as np
import matplotlib.pyplot as plt  # Importar matplotlib para graficar
import operator
from scipy.io import savemat
from scipy.interpolate import interp1d
from typing import List, Dict

class Signal:
    def __init__(self, dbc_path=None):
        # Cargar el archivo DBC solo si se proporciona la ruta
        if dbc_path:
            self.db = cantools.database.load_file(dbc_path)
            print(f"Loaded DBC: {dbc_path}")
        else:
            self.db = None  # Inicializar sin base de datos si no se proporciona dbc_path

        # Definir las operaciones y precedencia
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

    def __add__(self, otra):
        """Sobrecarga del operador + para sumar dos señales."""
        return self._operate(otra, '+')

    def __sub__(self, otra):
        """Sobrecarga del operador - para restar dos señales."""
        return self._operate(otra, '-')

    def __mul__(self, otra):
        """Sobrecarga del operador * para multiplicar dos señales."""
        return self._operate(otra, '*')

    def __truediv__(self, otra):
        """Sobrecarga del operador / para dividir dos señales."""
        return self._operate(otra, '/')

    def _operate(self, otra, operador):
        """Método genérico para realizar operaciones entre señales."""
        if not isinstance(otra, Signal):
            raise ValueError("Solo se pueden operar instancias de Signal.")

        # Ajustar las señales al mismo tamaño
        max_len = max(len(self.valores), len(otra.valores))
        valores_self = self._interpolate(self.valores, max_len)
        valores_otra = self._interpolate(otra.valores, max_len)

        # Realizar la operación correspondiente
        resultado_valores = self.operations[operador](np.array(valores_self), np.array(valores_otra))
        nuevo_nombre = f"({self.nombre} {operador} {otra.nombre})"
        
        # Crear y devolver una nueva instancia de Signal
        nueva_signal = Signal()  # Inicializa sin cargar DBC
        nueva_signal.db = self.db  # Asigna la base de datos actual
        nueva_signal.nombre = nuevo_nombre
        nueva_signal.valores = resultado_valores.tolist()  # Guardar como lista

        return nueva_signal

    def _interpolate(self, valores, new_size):
        """Interpolar valores a un nuevo tamaño."""
        if len(valores) == 0:
            return [0] * new_size  # Si la lista está vacía

        x = np.linspace(0, 1, len(valores))
        x_new = np.linspace(0, 1, new_size)
        f = interp1d(x, valores, kind='linear', fill_value="extrapolate")
        return f(x_new).tolist()

    def get_signal_values(self, signal_name, log_path):
        """Obtiene los valores de la señal desde el archivo de log."""
        pattern = r'\((?P<timestamp>\d+\.\d{6})\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        
        # Abrir el log
        try:
            with open(log_path, 'r') as file:
                log = file.read()
        except FileNotFoundError:
            print(f"Error: El archivo de log '{log_path}' no se encontró.")
            return []
        except Exception as e:
            print(f"Error al abrir el archivo de log: {e}")
            return []

        # Compilar el patrón de regex
        regex = re.compile(pattern)
        grouped_decoded = defaultdict(lambda: defaultdict(lambda: None))
        timestamps = set()

        # Hacer los matches y decodificar
        for match in regex.finditer(log):
            timestamp = float(match.group("timestamp"))
            timestamps.add(timestamp)

            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)

            try:
                msg_data = bytearray.fromhex(match.group("data"))
                log_decode = self.db.decode_message(msg_id, msg_data)
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[timestamp][key] = value
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        # Ordenar los timestamps
        sorted_timestamps = sorted(timestamps)

        # Crear lista con los datos de señales alineados con los timestamps
        signal_values = [grouped_decoded[timestamp].get(signal_name, np.nan) for timestamp in sorted_timestamps]
        return sorted_timestamps, signal_values

    def evaluate_expression(self, expression, log_path):
        """Evalúa una expresión que puede contener señales y operadores."""
        tokens = self._tokenize(expression)
        rpn = self._shunting_yard(tokens)
        return self._evaluate_rpn(rpn, log_path)

    def _tokenize(self, expression):
        """Divide la expresión en tokens."""
        tokens = []
        token = ''
        for char in expression:
            if char in '()+-*/':
                if token:
                    tokens.append(token.strip())
                    token = ''
                tokens.append(char)
            else:
                token += char
        if token:
            tokens.append(token.strip())
        return tokens

    def _shunting_yard(self, tokens):
        """Convierte la expresión a notación de polaca inversa."""
        output = []
        operators = []
        for token in tokens:
            if token in self.operations:  # Si es un operador
                while (operators and operators[-1] in self.operations and
                       self.precedence[operators[-1]] <= self.precedence[token]):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                operators.pop()  # Quitar '('
            else:  # Si es una señal
                output.append(token)
        while operators:
            output.append(operators.pop())
        return output

    def _evaluate_rpn(self, rpn, log_path):
        """Evalúa la expresión en notación de polaca inversa."""
        stack = []
        for token in rpn:
            if token in self.operations:
                otra = stack.pop()
                una = stack.pop()
                # Obtener los valores de las señales
                timestamp_una, valores_una = self.get_signal_values(una, log_path)
                timestamp_otra, valores_otra = self.get_signal_values(otra, log_path)
                signal_una = Signal()
                signal_otra = Signal()
                signal_una.nombre = una
                signal_otra.nombre = otra
                signal_una.valores = valores_una
                signal_otra.valores = valores_otra

                # Operar y almacenar resultados
                resultado = signal_una._operate(signal_otra, token)
                stack.append(resultado)
            else:
                # Añadir la señal correspondiente a la pila
                stack.append(token)
        return stack[0]

    def plot_signals(self, df, signals_to_plot):
        """Generar gráficos de las señales especificadas"""
        for signal in signals_to_plot:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
        plt.xlabel('Timestamp')
        plt.ylabel('Value')
        plt.title('Signal Values over Time')
        plt.legend()
        plt.show()

    def export_to_excel(self, df, output_file):
        """Exportar el DataFrame a un archivo Excel"""
        df.to_excel(output_file, index=False)
        print(f"Datos exportados a Excel: {output_file}")

    def export_to_matlab(self, df, output_file):
        """Exportar el DataFrame a un archivo MATLAB"""
        savemat(output_file, {col: df[col].to_numpy() for col in df.columns})
        print(f"Datos exportados a MATLAB: {output_file}")

    def decode_log(self, log_path: str, output_file: str, output_format: str, signals_to_plot=None):
        """Decodificar el archivo de log usando el archivo DBC y generar los resultados"""
        pattern = r'\((?P<timestamp>\d+\.\d{6})\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        
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
        grouped_decoded = defaultdict(lambda: defaultdict(lambda: None))
        timestamps = set()

        # Hacer los matches y decodificar
        for match in regex.finditer(log):
            timestamp = float(match.group("timestamp"))
            timestamps.add(timestamp)

            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)

            try:
                msg_data = bytearray.fromhex(match.group("data"))
                log_decode = self.db.decode_message(msg_id, msg_data)
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[timestamp][key] = value
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        # Ordenar los timestamps
        sorted_timestamps = sorted(timestamps)

        # Crear DataFrame con los datos decodificados
        data = {'Timestamp': sorted_timestamps}
        for key in grouped_decoded[sorted_timestamps[0]].keys():
            data[key] = [grouped_decoded[timestamp].get(key, np.nan) for timestamp in sorted_timestamps]

        df = pd.DataFrame(data)

        # Exportar a Excel si se especifica
        if output_format.lower() == 'excel':
            self.export_to_excel(df, output_file)
        elif output_format.lower() == 'matlab':
            self.export_to_matlab(df, output_file)
        else:
            print(f"Formato de salida '{output_format}' no soportado.")

        # Graficar las señales si se especifica
        if signals_to_plot:
            self.plot_signals(df, signals_to_plot)

# Ejemplo de uso
if __name__ == "__main__":
    # Crear instancia de Signal
    signal = Signal(dbc_path='ruta/al/archivo.dbc')

    # Evaluar una expresión con nombres de señales
    expression = "V_tot + Barometri"  # Reemplaza con los nombres de las señales deseadas
    resultado_signal = signal.evaluate_expression(expression, 'ruta/al/archivo.log')
    print(f"Resultado de la expresión '{expression}': {resultado_signal.nombre} = {resultado_signal.valores}")

    # Decodificar log
    signal.decode_log('ruta/al/archivo.log', 'resultado.xlsx', 'excel', signals_to_plot=['Signal1', 'Signal2'])







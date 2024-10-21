import numpy as np
import operator
import cantools
from scipy.interpolate import interp1d

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
        
        self.nombre = ""
        self.valores = []
        self.signals = {}  # Diccionario para almacenar las señales

    def add_signal(self, name, values):
        """Método para añadir señales al diccionario."""
        signal = Signal()  # No se pasa dbc_path aquí
        signal.db = self.db  # Asigna la base de datos directamente
        signal.nombre = name
        signal.valores = values
        self.signals[name] = signal

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
            # Si la lista está vacía, devolver una lista de ceros del nuevo tamaño
            return [0] * new_size

        x = np.linspace(0, 1, len(valores))  # Espacios originales
        x_new = np.linspace(0, 1, new_size)  # Nuevos espacios
        f = interp1d(x, valores, kind='linear', fill_value="extrapolate")
        return f(x_new).tolist()

    def evaluate_expression(self, expression):
        """Evalúa una expresión que puede contener señales y operadores."""
        tokens = self._tokenize(expression)
        rpn = self._shunting_yard(tokens)
        return self._evaluate_rpn(rpn)

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

    def _evaluate_rpn(self, rpn):
        """Evalúa la expresión en notación de polaca inversa."""
        stack = []
        for token in rpn:
            if token in self.operations:
                otra = stack.pop()
                una = stack.pop()
                # Asegurarse de que 'una' y 'otra' son instancias de Signal
                resultado = una._operate(otra, token)
                stack.append(resultado)
            else:
                # Añadir la señal correspondiente a la pila
                stack.append(self._get_signal(token))
        return stack[0]

    def _get_signal(self, token):
        """Obtiene la señal correspondiente al token."""
        # Busca la señal en el diccionario de señales
        if isinstance(token, Signal):
            return token
        if token in self.signals:
            return self.signals[token]
        else:
            raise KeyError(f"La señal '{token}' no se encontró en el diccionario.")

# Ejemplo de uso
if __name__ == "__main__":
    signals = Signal("./TER.dbc")
    signals.add_signal("Señal 1", [6, 0, 4, 2, 5])
    signals.add_signal("Señal 2", [25, 20, 3, 0, 1])
    signals.add_signal("Señal 3", [5, 5, 5, 5, 2])
    signals.add_signal("Señal 4", [2, 2, 2, 2, 2])

    resultado = signals.evaluate_expression("Señal 1 + Señal 2 * Señal 3 - Señal 4")
    print(resultado.nombre)
    print(resultado.valores)




















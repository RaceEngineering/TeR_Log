import re
import cantools
import json
#import numpy
#import typing

#class logDecoder:
   # def __init__(self, dbcPatch : str, sigList : list = None ):
      #  self.db = cantools.database.load_file(dbcPatch)
      #  self.signalList = sigList

   # def decodeLog(self,logPath : str):



# Define the pattern to obtain a match in the log
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")


# Open Log File
file = open("RUN0.log",'r')
log = file.read()

# Compile the regex pattern
regex = re.compile(pattern)

# Capture the matches using `re.finditer`:
for match in regex.finditer(log):
    msg = {
        "bus" : match.group(1),
        "id" : int(match.group(2),16),
        "DLC" : int(match.group(3)),
        "data" : bytearray.fromhex(match.group(4))   #cambiandolo de numeros hexadecimales a 
    }
    print(db.decode_message(msg["id"], msg["data"]))

log_decode = db.decode_message(msg["id"], msg["data"])
print(type(log_decode))
print("Hola")

with open('log_decode_str.txt', 'w') as archivo:
    for key, value in log_decode.items():
        archivo.write(f'{key}: {value}\n')
        archivo.write('\n')

file = open("log_decode_str.txt",'r')
log_decode_str= file.read()
print(type(log_decode_str))
print(log_decode_str)
print("Hola")


def extract_data(log_decode_str):   #Crear Funcion que coge un texto y devuelve un diccionario con mis nombres y valores
    # Expresion regex para pillar los putos nombres y valores
    pattern = r"'([A-Za-z_]+)':\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)"
    
    # Buscar las palabras en el texto y devulve tuplas
    encontrados = re.findall(pattern, log_decode_str)
    
    # Crear un diccionario para almacenar los datos
    log_dict = {}
    
    for match in encontrados:
        key, value = match #Separar tupla en clave y valor
        value = float(value) #Convertir el valor en float
        
        # Si la clave no está en el diccionario, crear una nueva entrada con una lista
        if key not in log_dict:
            log_dict[key] = []
        
        # Añadir el valor a la lista de nombres de variables
        log_dict[key].append(value)
    
    return log_dict

# Texto de ejemplo
text = """
{'PITCH': -24.69, 'ROLL': 26.12, 'YAW': 121.41}
{'Roll_Rate_x': 2.0460000000000003, 'Pitch_Rate_y': 2.025, 'Yaw_Rate_z': 2.935}
{'Latitude': 0.0, 'Longitude': 0.0}
{'Altidude': 0.0, 'Barometric_Pressure': -0.0012416}
{'a_x': -8.365, 'a_y': -4.239, 'a_z': -3.834}
{'Heading': -2.3000000000000003}
{'v_x': 0.0, 'v_y': 0.0, 'v_z': 0.0}
{'Status': -32640, 'PosU': 0.0, 'VelU': 0.0}
{'PITCH': -24.13, 'ROLL': 26.96, 'YAW': 126.08}
{'Roll_Rate_x': 2.519, 'Pitch_Rate_y': 1.837, 'Yaw_Rate_z': 3.121}
{'Latitude': 0.0, 'Longitude': 0.0}
{'Altidude': 0.0, 'Barometric_Pressure': -0.0007999999999999999}
{'a_x': -4.852, 'a_y': -4.805, 'a_z': -4.909}
{'Heading': -2.34}
{'v_x': 0.0, 'v_y': 0.0, 'v_z': 0.0}
{'Status': 128, 'PosU': 0.0, 'VelU': 0.0}
{'PITCH': -24.67, 'ROLL': 28.060000000000002, 'YAW': 130.16}
{'Roll_Rate_x': 2.32, 'Pitch_Rate_y': 0.588, 'Yaw_Rate_z': 3.104}
{'Latitude': 0.0, 'Longitude': 0.0}
{'Altidude': 0.0, 'Barometric_Pressure': -0.0012416}
{'a_x': -5.224, 'a_y': -4.923, 'a_z': -5.281}
{'Heading': -2.38}
{'v_x': 0.0, 'v_y': 0.0, 'v_z': 0.0}
{'Status': 128, 'PosU': 0.0, 'VelU': 0.0}
{'PITCH': -25.41, 'ROLL': 28.32, 'YAW': 131.91}
{'Roll_Rate_x': 2.126, 'Pitch_Rate_y': 0.56, 'Yaw_Rate_z': 3.86}
{'Latitude': 0.0, 'Longitude': 0.0}
{'Altidude': 0.0, 'Barometric_Pressure': -0.0014528}
{'a_x': -1.965, 'a_y': -6.521, 'a_z': -7.4670000000000005}
{'Heading': -2.41}
"""

# Ejecutar la función
result = extract_data(log_decode_str) #llamar funcion
print(result)



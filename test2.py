import re
import cantools
import json

# Define the pattern to obtain a match in the log
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")

# Open Log File
with open("RUN0.log", 'r') as file:
    log=file.read()

# Compile the regex pattern
regex = re.compile(pattern)

# Crear un diccionario para almacenar los resultados decodificados
log_dic = {}

# Capturar las coincidencias usando `re.finditer`
for match in regex.finditer(log):
    msg = {
        "bus": match.group(1),
        "id": int(match.group(2), 16),
        "DLC": int(match.group(3)),
        "data": bytearray.fromhex(match.group(4))  # Convertir de hexadecimales a bytes
    }
    
    # Decodificar el mensaje
    decoded_message = db.decode_message(msg["id"], msg["data"])

decoded_message_str = json.dumps(decoded_message)
print(decoded_message_str)

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

# Ejecutar la función
result = extract_data(log_decode_str) #llamar funcion
print(result)



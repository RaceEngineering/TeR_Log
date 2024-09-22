import cantools
import re

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")

# Patrón para extraer los mensajes del archivo de log
PATTERN = r'(can0\s+)(\d+)(\s+\[\d\]\s+)([A-Fa-f0-9\s]+)'
msgParser = re.compile(PATTERN)

# Abrir el archivo de log
with open("./RUN0.log", "r") as log:
  # Se añade "with" para un mejor manejo del archivo
    # Procesar cada línea del archivo de log
    for line in log:
        # Intentar hacer coincidir la línea con el patrón
        msg_groups = re.match(PATTERN, line)
        if msg_groups:
            can_id = int(msg_groups[2])  # El ID del mensaje CAN (en decimal)
            data = msg_groups[4].strip().split()  # Los datos en formato hexadecimal
            data_bytes = bytes(int(byte, 16) for byte in data)  # Convertir los datos a bytes

            # Buscar el mensaje en la base de datos .dbc usando el ID
            try:
                decoded_message = db.decode_message(can_id, data_bytes)
                print(f"Mensaje CAN ID: {can_id}")
                print("Datos decodificados:")
                for signal_name, signal_value in decoded_message.items():
                    print(f"  {signal_name}: {signal_value}")
                print()
            except KeyError:
                print(f"ID {can_id} no encontrado en el archivo DBC o no decodificable.")
        else:
            print("Invalid Line")
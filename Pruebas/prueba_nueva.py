import cantools
import re

# Cargar el archivo DBC
db = cantools.database.load_file('TER.dbc')

# Crear un diccionario para almacenar las señales y sus datos
signals_data = {}

# Leer el archivo RUN0.log
with open('RUN0.log', 'r') as log_file:
    for line in log_file:
        parts = line.split()
        can_id = int(parts[1], 16)
        data = bytes.fromhex(''.join(parts[3:11]))

        # Decodificar el mensaje utilizando el archivo DBC
        try:
            message = db.get_message_by_frame_id(can_id)
            decoded_signals = message.decode(data)
            
            # Almacenar los datos de cada señal en el diccionario
            for signal_name, signal_value in decoded_signals.items():
                if signal_name not in signals_data:
                    signals_data[signal_name] = []
                signals_data[signal_name].append(signal_value)
        except KeyError:
            # Ignorar si la ID no se encuentra en el archivo DBC
            continue

# Imprimir o procesar el diccionario final con las señales y sus datos
for signal, values in signals_data.items():
    print(f"{signal}: {values}")

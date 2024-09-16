import re
import cantools
#import json
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

#log_decode = db.decode_message(msg["id"], msg["data"])
#log_decode_str = json.dumps(log_decode)
#log_dic= {}

# Expresion para coger el nombre de la variable y su valor
#pattern2 = r" '([A-Za-z_]+)':\s*(-?\d+(?:\.\d+)?(?:e-?\d+)?)"

# Compile the regex pattern
#regex = re.compile(pattern2)

#Coger coindencias y guardar en diccionario
#for match in regex.finditer(log_decode_str):
  
        #variable = match.group(1)  # Captura el nombre de la variable
        #valor = float(match.group(2))
        #log_dic[variable] = valor 
   

#print(log_dic)
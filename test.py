import re
import cantools
import numpy
import typing

class logDecoder:
    def __init__(self, dbcPatch : str, sigList : list = None ):
        self.db = cantools.database.load_file(dbcPatch)
        self.signalList = sigList

    def decodeLog(self,logPath : str):
        




# Define the pattern
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'
# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")


# Open Log File
file = open("RUN0.log",'r')
log = file.read()

# Compile the regex pattern
regex = re.compile(pattern)

# If you want to capture the matches in a different way, you can use `re.finditer`:
for match in regex.finditer(log):
    msg = {
        "bus" : match.group(1),
        "id" : int(match.group(2),16),
        "DLC" : int(match.group(3)),
        "data" : bytearray.fromhex(match.group(4))
    }
    print(db.decode_message(msg["id"], msg["data"]))

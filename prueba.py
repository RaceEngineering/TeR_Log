import cantools
import re
db = cantools.db.load_file("./TeR_DATABASES/TER.dbc")


PATTERN = r"(can0\s+)(\d+)(\s+\[8\]\s+)([A-Fa-f0-9\s]+)"

# cargamos el archivo

log = open("./RUN0.log")
for line in log:
    msgGroups = re.match(PATTERN,line)
    if msgGroups:
        print(msgGroups[1])



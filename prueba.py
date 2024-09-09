import cantools
db = cantools.db.load_file("./TeR_DATABASES/TER.dbc")

print(db.messages)

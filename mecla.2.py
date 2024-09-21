import re
import cantools
import csv
from collections import defaultdict

# Define the pattern to obtain a match in the log
pattern = r'(can0\s+)(\d+)\s+\[(\d)\]\s+([A-F0-9\s]+)'

# Cargar el archivo .dbc
db = cantools.database.load_file("./TER.dbc")

# Open Log File
with open("RUN0.log", 'r') as file:
    log = file.read()

# Compile the regex pattern
regex = re.compile(pattern)

# Dictionary to group decoded messages
grouped_decoded = defaultdict(list)

# Capture the matches using `re.finditer`:
for match in regex.finditer(log):
    msg = {
        "data": bytearray.fromhex(match.group(4)),
        "id": int(match.group(2), 16)
    }
    
    # Decode the message
    log_decode = db.decode_message(msg["id"], msg["data"])
    
    # Group values by key
    for key, value in log_decode.items():
        if isinstance(value, (int, float)):
            grouped_decoded[key].append(value)

# Prepare to write to CSV
with open('decoded_log.csv', mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)

    # Write grouped decoded messages to CSV
    for key, values in grouped_decoded.items():
        writer.writerow([key, values])

print("Decoding completed and saved to decoded_log.csv")

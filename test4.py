import re


# Cadena de texto de ejemplo
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
def extract_keys_from_text(text):
    pattern3 = r'([A-Za-z_]+)' 
    matches = re.findall(pattern3, text)
    result_dict = {key: None for key in set(matches)}

    return result_dict

result = extract_keys_from_text(text)
print(result)
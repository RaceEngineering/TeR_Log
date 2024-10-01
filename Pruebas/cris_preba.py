
import pandas as pd  

df = pd.read_csv('log_decodificado.csv')

#nueva_variable = df['Roll_Rate_x']

nueva_variable = df.iloc[1]


print(nueva_variable)




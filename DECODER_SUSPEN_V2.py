import re
import cantools
import pandas as pd
from collections import defaultdict
import xlsxwriter
import numpy as np
import matplotlib.pyplot as plt  # Importar matplotlib para graficar
import operator
from scipy.io import savemat
from typing import List, Dict

class Signal:
    def __init__(self, dbc_path: str):
        # Cargar el archivo DBC
        try:
            self.db = cantools.database.load_file(dbc_path)
            print(f"Loaded DBC: {dbc_path}")
        except Exception as e:
            print(f"Error loading DBC file: {e}")
            raise

        # Imprimir todos los IDs y sus nombres de mensajes en el DBC
        self._print_message_ids()
        
        #METER OPERADORES Y PREFERENCIAS
        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }
        # Definir la precedencia de operadores
        self.precedence = {
            '+': 2,
            '-': 2,
            '*': 1,
            '/': 1
        }
         # 📌 Cargar la tabla de referencia desde "CALCULO ROLL.xlsx"
        try:
            self.xlsx_data = pd.read_excel("CALCULO ROLL.xlsx", sheet_name=0)
            self.CLCULOROLL1_x = self.xlsx_data.iloc[:, 1].values  # Segunda columna: desplazamiento de referencia
            self.CLCULOROLL1_y = self.xlsx_data.iloc[:, 0].values  # Primera columna: roll correspondiente

            self.xlsx_data_pitch = pd.read_excel("CALCULO ROLL.xlsx", sheet_name=1)
            self.CLCULOPITCH1_x = self.xlsx_data_pitch.iloc[:, 1].values  
            self.CLCULOPITCH1_y = self.xlsx_data_pitch.iloc[:, 0].values  

            print("✅ Archivo 'CALCULO ROLL.xlsx' cargado correctamente.")


        except Exception as e:
            print(f"❌ Error al cargar 'CALCULO ROLL.xlsx': {e}")
            self.CLCULOROLL1_x = []
            self.CLCULOROLL1_y = []
            self.CLCULOPITCH1_x= []
            self.CLCULOPITCH1_y = []

    def _print_message_ids(self):
        """Imprime los IDs de los mensajes definidos en el DBC."""
        print("Message IDs defined in the DBC:")
        for message in self.db.messages:
            print(f"ID: {message.frame_id} ({message.name})")
    
    def calcular_roll_nuevo(self, df):
        """
        Calcula la nueva columna 'ROLL_nuevo' basada en las columnas 'FrontSuspL' y 'FrontSuspR'.
        """
        if "FrontSuspL" not in df.columns or "FrontSuspR" not in df.columns:
            print("❌ Error: Las columnas 'FrontSuspL' y 'FrontSuspR' no están en el DataFrame.")
            return df

        # Calcular la diferencia delta
        df["delta"] = df["FrontSuspL"] - df["FrontSuspR"]
        df["ROLL_nuevo"] = np.zeros(len(df))

        # Bucle para asignar valores de ROLL_nuevo basados en la tabla de referencia
        for i in range(len(df)):
            disp_abs = abs(df.loc[i, "delta"])
            dif_min = np.inf
            fila_seleccionada = 0

            # Buscar el valor más cercano en CLCULOROLL1_x
            for j in range(len(self.CLCULOROLL1_x)):
                dif_actual = abs(disp_abs - abs(self.CLCULOROLL1_x[j]))
                if dif_actual < dif_min:
                    dif_min = dif_actual
                    fila_seleccionada = j

            # Asignar el valor de ROLL correspondiente
            df.loc[i, "ROLL_nuevo"] = self.CLCULOROLL1_y[fila_seleccionada]

            # Si delta es negativo, invertir el signo de ROLL
            if df.loc[i, "delta"] < 0:
                df.loc[i, "ROLL_nuevo"] = -df.loc[i, "ROLL_nuevo"]

        # Eliminar la columna temporal 'delta'
        df.drop(columns=["delta"], inplace=True)

        return df
    
    def calcular_pitch_nuevo(self, df):
        """ Calcula la nueva columna 'PITCH_nuevo' basada en el promedio de suspensiones delanteras y traseras. """
        if not all(col in df.columns for col in ["FrontSuspL", "FrontSuspR", "RearSuspL", "RearSuspR"]):
            print("❌ Error: No se encontraron todas las columnas necesarias para calcular 'PITCH_nuevo'.")
            return df

        df["delta_pitch"] = (df["FrontSuspL"] + df["FrontSuspR"]) / 2 - (df["RearSuspL"] + df["RearSuspR"]) / 2
        df["PITCH_nuevo"] = np.zeros(len(df))

        for i in range(len(df)):
            disp_abs = abs(df.loc[i, "delta_pitch"])
            dif_min = np.inf
            fila_seleccionada = 0

            for j in range(len(self.CLCULOPITCH1_x)):
                dif_actual = abs(disp_abs - abs(self.CLCULOPITCH1_x[j]))
                if dif_actual < dif_min:
                    dif_min = dif_actual
                    fila_seleccionada = j

            df.loc[i, "PITCH_nuevo"] = self.CLCULOPITCH1_y[fila_seleccionada]
            if df.loc[i, "delta_pitch"] < 0:
                df.loc[i, "PITCH_nuevo"] = -df.loc[i, "PITCH_nuevo"]

        df.drop(columns=["delta_pitch"], inplace=True)
        return df


    def _write_to_csv(self, df: pd.DataFrame, csv_final: str):
        """Guardar los datos en formato CSV para evitar problemas con archivos Excel grandes."""
        df.to_csv(csv_final, index=False)
        print(f"Decoding completed and saved to {csv_final}")
    
    def _write_to_mat(self, df: pd.DataFrame, mat_file: str):
        """Guardar los datos en formato .mat para MATLAB."""
        mat_data = {col: df[col].values for col in df.columns}
        savemat(mat_file, mat_data)
        print(f"Data saved to {mat_file} in MATLAB format.")
    
    def _write_to_excel_line_by_line(self, df: pd.DataFrame, excel_final: str, selected_signals: list, plot_path_rollgradient: str = None, plot_path_aceleracion_lateralVSroll: str = None,plot_path_aceleracion_longitudinalVSpitch: str = None, plot_path_tempsVSsteeringVSaceleracion_latVSaceleracion_long: str = None, plot_path_velVSaceleracion_latVSsteeringVS_SAchassis: str = None, plot_path_velVSaceleracion_latVSsteeringVSyow_rate: str = None):
        """Escribir línea por línea en Excel usando xlsxwriter e insertar gráfico en una segunda hoja."""

        """Guardar datos en un Excel con dos hojas:
           - 'Selected Data': Solo las señales seleccionadas por el usuario, si existen.
           - 'Full Data': Todos los datos del DataFrame."""
        
        df_clean = df.fillna('').replace([np.inf, -np.inf], '')  # Reemplazar NaN e inf por cadena vacía
        workbook = xlsxwriter.Workbook(excel_final)
        
        # Hoja 1: Datos seleccionados
        worksheet_selected = workbook.add_worksheet("Selected Data")
        available_signals = [sig for sig in selected_signals if sig in df_clean.columns]  # Filtrar señales existentes
        
        if available_signals:
            selected_df = df_clean[available_signals]
        else:
            selected_df = pd.DataFrame()  # Si no hay señales disponibles, crear un DataFrame vacío

        # Escribir encabezados si hay datos seleccionados
        for col_num, value in enumerate(selected_df.columns):
            worksheet_selected.write(0, col_num, value)

        # Escribir datos
        for row_num, row in enumerate(selected_df.itertuples(index=False), 1):
            worksheet_selected.write_row(row_num, 0, row)

        # Hoja 2: Todos los datos
        worksheet_full = workbook.add_worksheet("Full Data")

        # Escribir encabezados
        for col_num, value in enumerate(df_clean.columns):
            worksheet_full.write(0, col_num, value)

        # Escribir datos
        for row_num, row in enumerate(df_clean.itertuples(index=False), 1):
            worksheet_full.write_row(row_num, 0, row)

        # Insertar la gráfica en la segunda hoja si se proporcionó el gráfico
        if plot_path_rollgradient:
            worksheet_plot = workbook.add_worksheet("Roll Gradient")
            worksheet_plot.insert_image('B3', plot_path_rollgradient)  # Insertar la grafico aceleracion_lateralVSroll en la celda B2 de la segunda hoja

        if plot_path_aceleracion_lateralVSroll:
            worksheet_plot = workbook.add_worksheet("Aceleracionlat VS Roll")
            worksheet_plot.insert_image('B4', plot_path_aceleracion_lateralVSroll)  # Insertar la grafico aceleracion_lateralVSroll en la celda B2 de la segunda hoja

        if plot_path_aceleracion_longitudinalVSpitch:
            worksheet_plot = workbook.add_worksheet("Aceleracionlong VS Pitch")
            worksheet_plot.insert_image('B5', plot_path_aceleracion_longitudinalVSpitch)  # Insertar la grafico aceleracion_longitudinalVSpitch en la celda B3 de la segunda hoja

        if plot_path_tempsVSsteeringVSaceleracion_latVSaceleracion_long:
            worksheet_plot = workbook.add_worksheet("TempsVS.SteerVS.a_latVS.a_long")
            worksheet_plot.insert_image('B6', plot_path_tempsVSsteeringVSaceleracion_latVSaceleracion_long)  # Insertar la grafico Temperaturas VS Steering VS Aceleración lateral VS Aceleración longitudinal en la celda B4 de la segunda hoja
        
        if plot_path_velVSaceleracion_latVSsteeringVS_SAchassis:
            worksheet_plot = workbook.add_worksheet("VelVS.a_latVS.SteerVS.SA")
            worksheet_plot.insert_image('B7', plot_path_velVSaceleracion_latVSsteeringVS_SAchassis)  # Insertar la grafico Velocidad VS Aceleración lateral VS Steering VS Slip Angle en la celda B5 de la segunda hoja
        
        if plot_path_velVSaceleracion_latVSsteeringVSyow_rate:
            worksheet_plot = workbook.add_worksheet("VelVS.a_latVS.SteerVS.YowRate")
            worksheet_plot.insert_image('B8', plot_path_velVSaceleracion_latVSsteeringVSyow_rate)  # Insertar la grafico Velocidad VS Aceleración lateral VS Steering VS Yow Rate en la celda B6 de la segunda hoja
        
        workbook.close()

        print(f"Decoding completed and saved to {excel_final}")
    
    def _write_to_ascii(self, df: pd.DataFrame, ascii_file: str):
        """Guardar los datos en formato ASCII (archivo de texto)."""
        with open(ascii_file, 'w') as file:
            # Escribir los encabezados de las columnas
            file.write('\t'.join(df.columns) + '\n')
            # Escribir los datos fila por fila
            for _, row in df.iterrows():
                file.write('\t'.join(map(str, row.values)) + '\n')

        print(f"Data saved to {ascii_file} in ASCII format.")

    def plot_rollgradient(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con 'aceleracion_lat' en el eje X y el roll en el eje Y."""
        if 'a_y' not in df.columns:
            print("Warning: 'aceleracion_lat' no encontrado en los datos.")
            return
        
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['a_y'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Aceleración Lateral')
        plt.ylabel('Roll')
        plt.title('Roll Gradient')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()

    def plot_aceleracion_lateralVSroll(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Señales')
        plt.title('Aceleracion lateral VS Roll')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()

    def plot_aceleracion_longitudinalVSpitch(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Señales')
        plt.title('Aceleracion longitudinal VS Pitch')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()
    
    def plot_tempsVSsteeringVSaceleracion_latVSaceleracion_long(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Señales')
        plt.title('Temperaturas VS Steering VS Aceleración lateral VS Aceleración longitudinal')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()


    def plot_velVSaceleracion_latVSsteeringVS_SAchassis(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Señales')
        plt.title('Velocidad VS Aceleracion lateral VS Steering VS Slip Angle Chassis')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()
   
   
    def plot_velVSaceleracion_latVSsteeringVSyow_rate(self, df: pd.DataFrame, signals: list, output_plot: str = None):
        """Generar un gráfico con los 'timestamps' en el eje X y una o más señales en el eje Y."""
        
        plt.figure(figsize=(10, 6))
        for signal in signals:
            if signal in df.columns:
                plt.plot(df['Timestamp'], df[signal], label=signal)
            else:
                print(f"Warning: Signal '{signal}' not found in the data.")
        
        plt.xlabel('Timestamp')
        plt.ylabel('Señales')
        plt.title('Velocidad VS Aceleracion lateral VS Steering VS Yow Rate')
        plt.legend()
        plt.grid(True)
        
        # Guardar el gráfico si se proporciona un archivo de salida
        if output_plot:
            plt.savefig(output_plot)
            plt.close()
            print(f"Plot saved as {output_plot}")
        else:
            plt.show()

    def decode_log(self, log_path: str, output_file: str, output_format: str, selected_signals: list, rollgradient=None, aceleracion_lateralVSroll=None,aceleracion_longitudinalVSpitch=None, tempsVSsteeringVSaceleracion_latVSaceleracion_long=None,velVSaceleracion_latVSsteeringVS_SAchassis=None, velVSaceleracion_latVSsteeringVSyow_rate=None):
        """Decodificar el archivo de log usando el archivo DBC y generar los resultados"""
        pattern = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        
        # Abrir el log
        try:
            with open(log_path, 'r') as file:
                log = file.read()
        except FileNotFoundError:
            print(f"Error: El archivo de log '{log_path}' no se encontró.")
            return
        except Exception as e:
            print(f"Error al abrir el archivo de log: {e}")
            return

        # Compilar el patrón de regex
        regex = re.compile(pattern)

        # Diccionario para almacenar los datos decodificados
        grouped_decoded = defaultdict(lambda: defaultdict(lambda: None))
        timestamps = set()

        # Hacer los matches y decodificar
        for match in regex.finditer(log):
            timestamp = float(match.group("timestamp"))
            timestamps.add(timestamp)  # Agregar timestamp a la lista de timestamps

            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)  # Convertir ID a entero

            try:
                # Intentar convertir los datos hexadecimales
                msg_data = bytearray.fromhex(match.group("data"))
            except ValueError:
                continue

            try:
                # Decodificar el mensaje con el DBC
                log_decode = self.db.decode_message(msg_id, msg_data)

                # Agrupar los valores decodificados
                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[timestamp][key] = value
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        # Ordenar los timestamps
        sorted_timestamps = sorted(timestamps)

        # Obtener todas las señales presentes en los logs
        all_signals = set()
        for decoded_data in grouped_decoded.values():
            all_signals.update(decoded_data.keys())

        # Crear lista con los datos de señales alineados con los timestamps
        data = {'Timestamp': sorted_timestamps}
        for signal in all_signals:
            data[signal] = [grouped_decoded[timestamp].get(signal, np.nan) for timestamp in sorted_timestamps]

        # Crear DataFrame de Pandas
        df = pd.DataFrame(data)

        # Interpolar para cada señal
        for signal in all_signals:
            df[signal] = df[signal].interpolate(method='linear', limit_direction='both')
        
        if 'ANGLE' in df.columns:
            df['STEERING_ANGLE'] = (df['ANGLE'] * 360) / 101.65
            print("✅ Nueva columna agregada: 'STEERING_ANGLE'")
            print(df[['ANGLE', 'STEERING_ANGLE']].head())  # Verifica que los valores se están generando correctamente
        else:
            print("⚠️ La columna 'ANGLE' NO fue encontrada en el DataFrame.")


        df = self.calcular_roll_nuevo(df)
        df = self.calcular_pitch_nuevo(df)
        print(df[["ROLL_nuevo", "PITCH_nuevo"]].head())  # Verificación

        #Graficar Roll Gradient
        plot_file_rollgradient = None
        if rollgradient:
            plot_file_rollgradient = "rollgradient.png"
            self.plot_rollgradient(df, rollgradient, plot_file_rollgradient)

        # Graficar Aceleracion lateral VS Roll
        plot_file_aceleracion_lateralVSroll = None
        if aceleracion_lateralVSroll:
            plot_file_aceleracion_lateralVSroll = "aceleracion_lateralVSroll.png"
            self.plot_aceleracion_lateralVSroll(df, aceleracion_lateralVSroll, plot_file_aceleracion_lateralVSroll)
        
        # Graficar Aceleracion longitudinal VS Pitch
        plot_file_aceleracion_longitudinalVSpitch = None
        if aceleracion_longitudinalVSpitch:
            plot_file_aceleracion_longitudinalVSpitch = "aceleracion_longitudinalVSpitch.png"
            self.plot_aceleracion_longitudinalVSpitch(df, aceleracion_longitudinalVSpitch, plot_file_aceleracion_longitudinalVSpitch)

        # Graficar Temperaturas VS Steering VS Aceleración lateral VS Aceleración longitudinal
        plot_file_tempsVSsteeringVSaceleracion_latVSaceleracion_long = None
        if tempsVSsteeringVSaceleracion_latVSaceleracion_long:
            plot_file_tempsVSsteeringVSaceleracion_latVSaceleracion_long = "tempsVSsteeringVSaceleracion_latVSaceleracion_long.png"
            self.plot_tempsVSsteeringVSaceleracion_latVSaceleracion_long(df,tempsVSsteeringVSaceleracion_latVSaceleracion_long, plot_file_tempsVSsteeringVSaceleracion_latVSaceleracion_long)

        # Graficar Velocidad VS Aceleración lateral VS Steering VS Slip Angle Chasis
        plot_file_velVSaceleracion_latVSsteeringVS_SAchassis= None
        if velVSaceleracion_latVSsteeringVS_SAchassis:
            plot_file_velVSaceleracion_latVSsteeringVS_SAchassis = "velVSaceleracion_latVSsteeringVS_SAchassis.png"
            self.plot_velVSaceleracion_latVSsteeringVS_SAchassis(df, velVSaceleracion_latVSsteeringVS_SAchassis, plot_file_velVSaceleracion_latVSsteeringVS_SAchassis)
        
        # Graficar Velocidad VS Aceleración lateral VS Steering VS Yow Rate
        plot_file_velVSaceleracion_latVSsteeringVSyow_rate= None
        if velVSaceleracion_latVSsteeringVSyow_rate:
            plot_file_velVSaceleracion_latVSsteeringVSyow_rate = "velVSaceleracion_latVSsteeringVSyow_rate.png"
            self.plot_velVSaceleracion_latVSsteeringVSyow_rate(df, velVSaceleracion_latVSsteeringVSyow_rate, plot_file_velVSaceleracion_latVSsteeringVSyow_rate)
       
        # Guardar en el formato solicitado
        if output_format.lower() == 'xlsx':
            self._write_to_excel_line_by_line(df, output_file, selected_signals, plot_file_rollgradient, plot_file_aceleracion_lateralVSroll,plot_file_aceleracion_longitudinalVSpitch,plot_file_tempsVSsteeringVSaceleracion_latVSaceleracion_long,plot_file_velVSaceleracion_latVSsteeringVS_SAchassis, plot_file_velVSaceleracion_latVSsteeringVSyow_rate)
        elif output_format.lower() == 'csv':
            self._write_to_csv(df, output_file)
        elif output_format == 'mat':
            self._write_to_mat(df, output_file)
        elif output_format == 'ascii':
            self._write_to_ascii(df,output_file)
        else:
            print("Unsupported format")


# Uso del código
if __name__ == "__main__":
    try:
        decoder = Signal("./TER.dbc")
        # Decodificar y guardar los datos                            ######CAMBIAR PARAMETROS DE GRAFICASSS
        decoder.decode_log("RUN4 copy.log", "prueba_suspen_prueba.xlsx", "xlsx", selected_signals = ["Timestamp","a_y","a_x","v_x","v_y","Yaw_Rate_z","Front_Susp","STEERING_ANGLE", "flTemp","frTemp","rlTemp","rrTemp","BPPS","ROLL_nuevo","PITCH_nuevo"], rollgradient=["ROLL_nuevo"], aceleracion_lateralVSroll=["ROLL_nuevo","a_y"],aceleracion_longitudinalVSpitch=["PITCH_nuevo","a_x"],tempsVSsteeringVSaceleracion_latVSaceleracion_long=["flTemp","frTemp","rlTemp","rrTemp","STEERING_ANGLE","a_y","a_x"],velVSaceleracion_latVSsteeringVS_SAchassis=["v_x","STEERING_ANGLE","a_y","SAchassis"], velVSaceleracion_latVSsteeringVSyow_rate=["v_x","a_y","STEERING_ANGLE","Yaw_Rate_z"])  # Cambia Signal1, Signal2 por los nombres reales de las señales
    except Exception as e:
        print(f"Error during execution: {e}") ###
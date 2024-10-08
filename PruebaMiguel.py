import re
import cantools
import csv
from collections import defaultdict
from typing import List, Dict
import matplotlib.pyplot as plt
import pandas as pd
from scipy.io import savemat
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as OpenpyxlImage
from PIL import Image as PilImage
import operator
from scipy.interpolate import interp1d


class Signal:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        print(f"Loaded DBC: {dbc_path}")
        self._print_message_ids()

        self.operations = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv
        }

        self.precedence = {
            '+': 2,
            '-': 2,
            '*': 1,
            '/': 1
        }

    def _print_message_ids(self):
        """Imprime los IDs de los mensajes definidos en el DBC."""
        print("Message IDs defined in the DBC:")
        for message in self.db.messages:
            print(f"ID: {message.frame_id} ({message.name})")

    def _write_to_csv(self, grouped_decoded: Dict[str, List[float]], grouped_timestamps: Dict[str, List[float]], csv_final: str):
        # Crear el archivo CSV y escribir los datos junto con timestamps
        with open(csv_final, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Escribir encabezados
            writer.writerow(["Signal", "Timestamps", "Values"])
            for key, values in grouped_decoded.items():
                timestamps = grouped_timestamps.get(key, [""] * len(values))
                for i in range(len(values)):
                    writer.writerow([key, timestamps[i], values[i]])

        print(f"Decoding completed and saved to {csv_final}")
    
    def _write_to_xlsx(self, grouped_decoded: Dict[str, List[float]], grouped_timestamps: Dict[str, List[float]], xlsx_final:str, plot_save_path:str = None):
        data = {k: pd.Series(v) for k, v in grouped_decoded.items()}
        timestamps_data = {f"{k}_Timestamps": pd.Series(grouped_timestamps[k]) for k in grouped_timestamps}
        df = pd.DataFrame({**data, **timestamps_data})
        df.to_excel(xlsx_final, index=False)

        if plot_save_path:
            workbook = load_workbook(xlsx_final)
            sheet = workbook.create_sheet("Plot")

            img = PilImage.open(plot_save_path)
            img = img.convert("RGB")
            img.save("imagen_xlsx.png")

            image = OpenpyxlImage("imagen_xlsx.png")
            sheet.add_image(image, 'A1')
            workbook.save(xlsx_final)
        
        print(f"Decoding and plot saved to {xlsx_final}")

    def _write_to_mat(self, grouped_decoded: Dict[str, List[float]], grouped_timestamps: Dict[str, List[float]], mat_final: str):
        combined_data = {**grouped_decoded, **{f"{k}_Timestamps": v for k, v in grouped_timestamps.items()}}
        savemat(mat_final, combined_data)
        print(f"Decoding completed and saved to {mat_final}")

    def _write_to_ascii(self, grouped_decoded: Dict[str, List[float]], grouped_timestamps: Dict[str, List[float]], ascii_final: str):
        with open(ascii_final, mode='w') as ascii_file:
            signals = grouped_decoded.keys()
            ascii_file.write("\t".join(signals) + "\n")
            max_len = max(len(values) for values in grouped_decoded.values())
            for i in range(max_len):
                row = []
                for signal in signals:
                    value = grouped_decoded[signal][i] if i < len(grouped_decoded[signal]) else ""
                    timestamp = grouped_timestamps[signal][i] if i < len(grouped_timestamps[signal]) else ""
                    row.append(f"{timestamp}\t{value}")
                ascii_file.write("\t".join(row) + "\n")
        print(f"Decoding completed and saved to {ascii_final}")
    
    def _plot_signals(self, grouped_decoded: Dict[str, List[float]], signal_names: List[str], timestamps: List[float], save_path: str = None):
        plt.figure(figsize=(10, 5))
        for signal_name in signal_names:
            if signal_name in grouped_decoded:
                plt.plot(timestamps[:len(grouped_decoded[signal_name])], grouped_decoded[signal_name], label=signal_name)
            else:
                print(f"Signal {signal_name} not found in the decoded data.")
        plt.title("Signals Plot")
        plt.xlabel("Time(s)")
        plt.ylabel("Value")
        plt.legend()
        plt.grid(True)
        
        if save_path:
            plt.savefig(save_path)
            print(f"Plot saved to {save_path}")
        
        plt.show()
    
    def _apply_operation_with_precedence(self, expression: str, grouped_decoded: Dict[str, List[float]]) -> List[float]:
        def apply_operator(operands, operator):
            operand2 = operands.pop()
            operand1 = operands.pop()
            result = [self.operations[operator](a, b) for a, b in zip(operand1, operand2)]
            operands.append(result)

        tokens = re.split(r'(\s+|\+|\-|\*|\/|\(|\))', expression)
        tokens = [token.strip() for token in tokens if token.strip()]

        output = []
        operators = []

        for token in tokens:
            if token in grouped_decoded:
                output.append(grouped_decoded[token])
            elif re.match(r'\d+(\.\d+)?', token):
                output.append([float(token)] * len(next(iter(grouped_decoded.values()))))
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    apply_operator(output, operators.pop())
                operators.pop()
            elif token in self.operations:
                while (operators and operators[-1] in self.operations and
                       self.precedence[operators[-1]] <= self.precedence[token]):
                    apply_operator(output, operators.pop())
                operators.append(token)

        while operators:
            apply_operator(output, operators.pop())

        return output[0]


    def add_operation(self, grouped_decoded: Dict[str, List[float]], expression: str, result_name: str) -> Dict[str, List[float]]:
        result = self._apply_operation_with_precedence(expression, grouped_decoded)
        grouped_decoded[result_name] = result
        return grouped_decoded
    
    def decode_log(self, log_path: str, output_file: str, output_format: str, signals_to_plot: List[str] = None, plot_save_path: str = None, operations: List[Dict[str, str]] = None):
        pattern = r'\((?P<timestamp>\d+\.\d{6})\)\s+(?P<interface>\w+)\s+(?P<id>[0-9A-F]{3})\s*#\s*(?P<data>[0-9A-F]{2,16})'
        
        with open(log_path, 'r') as file:
            log = file.read()

        regex = re.compile(pattern)

        grouped_decoded = defaultdict(list)
        grouped_timestamps = defaultdict(list)
        timestamps = []

        for match in regex.finditer(log):
            msg_id_str = match.group("id")
            msg_id = int(msg_id_str, 16)

            try:
                msg_data = bytearray.fromhex(match.group("data"))
                timestamp = float(match.group("timestamp"))
                timestamps.append(timestamp)
            except ValueError:
                print(f"Error: Los datos '{match.group('data')}' no son válidos como hexadecimal. Se omite este mensaje.")
                pass

            try:
                log_decode = self.db.decode_message(msg_id, msg_data)
                print(f"Decoded Message ID: {msg_id}, Data: {msg_data.hex()} -> {log_decode}")

                for key, value in log_decode.items():
                    if isinstance(value, (int, float)):
                        grouped_decoded[key].append(value)
                        grouped_timestamps[key].append(timestamp)  # Asociar el timestamp a la señal
                    else:
                        print(f"Warning: Signal '{key}' has non-numeric value '{value}' in message ID {msg_id}. Skipping this value.")
            except KeyError:
                print(f"Warning: Message ID {msg_id_str} (decimal {msg_id}) is not defined in the DBC.")
            except Exception as e:
                print(f"Error decoding message with ID {msg_id_str} (decimal {msg_id}): {e}")

        if operations:
            for operation in operations:
                expression = operation['expression']
                result_name = operation.get('result_name', 'Result')
                grouped_decoded = self.add_operation(grouped_decoded, expression, result_name)

        if output_format == 'csv':
            self._write_to_csv(grouped_decoded, grouped_timestamps, output_file)
        elif output_format == 'ascii':
            self._write_to_ascii(grouped_decoded, grouped_timestamps, output_file)
        elif output_format == 'xlsx':
            self._write_to_xlsx(grouped_decoded, grouped_timestamps, output_file, plot_save_path=plot_save_path)
        elif output_format == 'mat':
            self._write_to_mat(grouped_decoded, grouped_timestamps, output_file)
        else:
            print("Unsupported format")

        if signals_to_plot:
            self._plot_signals(grouped_decoded, signals_to_plot, timestamps, save_path=plot_save_path)


if __name__ == "__main__":
    decoder = Signal("./TER.dbc")
    decoder.decode_log("RUN10.log", "RUN10.xlsx", "xlsx", signals_to_plot=["rrRPM", "rlRPM", "APPS_AV", "ANGLE"], plot_save_path="combined_plot.png")

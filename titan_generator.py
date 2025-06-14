import numpy as np
import os

# Generar portadora compleja fija (cos, sin) con frecuencia deseada
def generate_carrier_wave(frequency, num_samples, sample_rate):
    nyquist_frequency = sample_rate / 2
    if frequency > nyquist_frequency:
        raise ValueError(f"La frecuencia de la portadora ({frequency} Hz) no puede ser mayor que la frecuencia de Nyquist ({nyquist_frequency} Hz).")
    
    n = np.arange(num_samples)
    n_frequency = frequency / sample_rate

    cos_values = np.round(np.cos(2 * np.pi * n_frequency * n) * 30).astype(np.int8)
    sin_values = np.round(np.sin(2 * np.pi * n_frequency * n) * 30).astype(np.int8)

    interleaved_values = np.empty(2 * num_samples, dtype=np.int8)
    interleaved_values[0::2] = cos_values
    interleaved_values[1::2] = sin_values

    return interleaved_values

# Procesar una línea de bits (0, 1, 2) y generar la señal modulada
def process_line(bits, carrier, ints_per_symbol):
    on_times = {
        '1': int(ints_per_symbol * 3 / 4),
        '0': int(ints_per_symbol * 1 / 4),
    }

    signal = []

    for bit in bits:
        if bit not in ('0', '1', '2'):
            raise ValueError(f"Bit no válido encontrado: '{bit}'")

        if bit in ('0', '1'):
            on_time = on_times[bit]
            off_time = ints_per_symbol - on_time
            symbol = np.concatenate((carrier[:on_time], np.zeros(off_time, dtype=np.int8)))
        elif bit == '2':
            quarter = ints_per_symbol // 4
            symbol = np.concatenate([
                carrier[:quarter],
                np.zeros(quarter, dtype=np.int8),
                carrier[:quarter],
                np.zeros(ints_per_symbol - 3 * quarter, dtype=np.int8)  # cubrir todo
            ])
        
        signal.append(symbol)

    # Añadir silencio al final de la línea
    silence = np.zeros(4 * ints_per_symbol, dtype=np.int8)
    signal.append(silence)

    return np.concatenate(signal)

def main():
    # Parámetros fijos
    carrier_freq = 23437         # Frecuencia de portadora (Hz)
    fs = 2_000_000               # Frecuencia de muestreo (Hz)
    samples_per_symbol = 2380     # Muestras reales por símbolo
    ints_per_symbol = 2 * samples_per_symbol  # Total de enteros (I y Q) por símbolo

    input_file = 'soyyo.complex16s.txt'
    output_file = 'output_signal.complex16s'

    delay_symbols = 4  # n símbolos de silencio entre líneas
    delay_samples = delay_symbols * ints_per_symbol

    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"El archivo '{input_file}' no existe.")
    if os.stat(input_file).st_size == 0:
        raise ValueError(f"El archivo '{input_file}' está vacío.")

    with open(input_file, 'r') as f:
        lines = f.readlines()

    # Generar portadora de longitud completa por símbolo
    carrier = generate_carrier_wave(carrier_freq, samples_per_symbol, fs)

    output_signal = []

    for i, line in enumerate(lines):
        bits = line.strip().split(',')
        if i % 100 == 0:
            print(f"Procesando línea {i + 1}/{len(lines)}")
        signal = process_line(bits, carrier, ints_per_symbol)
        output_signal.append(signal)
        output_signal.append(np.zeros(delay_samples, dtype=np.int8))  # Silencio entre líneas

    output_signal = np.concatenate(output_signal)
    output_signal.tofile(output_file)
    print(f"Señal generada y guardada en {output_file}")

if __name__ == "__main__":
    main()

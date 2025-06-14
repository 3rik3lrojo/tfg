import numpy as np
from scipy.signal import hilbert, lfilter
from scipy.ndimage import binary_closing
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

DEBUG = False #Poner a true para el modo 

def eliminar_rebotes(signal_binaria, window_size=5):
    """
    Aplica un cierre binario para eliminar pequeños rebotes.
    `signal_binaria` debe ser un array de 0s y 1s.   
    """

    signal_binaria = np.array(signal_binaria, dtype=bool)
    return binary_closing(signal_binaria, structure=np.ones(window_size)).astype(int)

def conversion_pwm(filename, plot=False):
    #Primero leemos la señal en forma compleja
    yt = np.fromfile(filename, dtype=np.int8)
    I = yt[0::2]
    Q = yt[1::2]
    
    #Realmente nos interesa la magnitud de la portadora para descodificar ASk
    magnitud = np.hypot(I, Q)
    signal = magnitud / np.max(magnitud)
    signal[signal > 0.6] = 1
    signal[signal < 0.4] = 0

    # Filtrar rebotes con cierre binario para suavizar la señal PWM
    signal = eliminar_rebotes(signal, window_size=70)

    threshold_inicio = 0.8

    try:
        primer_indice = np.argmax(signal > threshold_inicio)
        if signal[primer_indice] <= threshold_inicio:
            return None
    except:
        return None

    return signal[primer_indice:]

def detectar_AB(signal, fs, start_idx, window_samples=588, plot_windows=False):
    threshold = 0.5
    ab_sequence = []
    i = start_idx
    count_B_consecutivas = 0
    max_Bs_para_resincronizar = 20

    if plot_windows:
        plt.figure(figsize=(15, 6))
        plt.plot(signal, 'black', linewidth=1.5, label='Señal PWM')
        plt.title("Ventanas de detección A/B (Resincronización con líneas rojas)")
        plt.xlabel("Muestras")
        plt.ylabel("Amplitud normalizada")
        plt.grid()
        plt.axhline(threshold, color='k', linestyle='--', label='Umbral')

    while i < len(signal) - window_samples:
        window = signal[i:i + window_samples]
        mean = np.mean(window)
        symbol = 'A' if mean > threshold else 'B'

        if plot_windows:
            color = 'green' if symbol == 'A' else 'blue'
            plt.axvspan(i, i+window_samples, alpha=0.2, color=color)
            plt.text(i + window_samples/2, 1.05, symbol,
                     ha='center', va='bottom', color=color, fontweight='bold')

        if symbol == 'B':
            count_B_consecutivas += 1
        else:
            count_B_consecutivas = 0

        if count_B_consecutivas >= max_Bs_para_resincronizar:
            nuevo_inicio = encontrar_inicio(signal[i:])
            if nuevo_inicio is not None:
                if plot_windows:
                    plt.axvline(x=i + nuevo_inicio, color='red', linestyle='-',
                                linewidth=2, alpha=0.8, label='Resincronización')

                i += nuevo_inicio
                count_B_consecutivas = 0
                ab_sequence.append('RESYNC')
                continue

        ab_sequence.append(symbol)
        i += window_samples

    if plot_windows:
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), loc="center right")
        plt.show()

    return ab_sequence

def codificar_bits_con_resincronizacion(ab_sequence):
    bits = [[]]
    j = 0
    i = 0

    while i + 3 < len(ab_sequence):
        if ab_sequence[i] == 'RESYNC':
            if len(bits[j]) > 0:
                bits.append([])
                j += 1
            i += 1
            continue

        grupo = ab_sequence[i:i+4]



        if grupo == ['A', 'B', 'A', 'B']:
            i += 4
        elif grupo == ['A', 'B', 'B', 'B']:
            bits[j].append(0)
            i += 4
        elif grupo == ['A', 'A', 'A', 'B']:
            bits[j].append(1)
            i += 4

        else:
            i += 1

    bits = [fila for fila in bits if len(fila) >= 20]
    return bits

def encontrar_inicio(signal):
    threshold_inicio = 0.8
    try:
        primer_indice = np.argmax(signal > threshold_inicio)
        if signal[primer_indice] <= threshold_inicio:
            return None
    except:
        return None
    return primer_indice

def procesar_archivo(filename, fs, plot_envolvente=False, plot_windows=False):
    signal_pwm = conversion_pwm(filename, plot=plot_envolvente)
    inicio_idx = encontrar_inicio(signal_pwm)

    if inicio_idx is None:
        raise ValueError("No se encontró un inicio válido.")

    ab_sequence = detectar_AB(signal_pwm, fs, inicio_idx, plot_windows=plot_windows)
    bits = codificar_bits_con_resincronizacion(ab_sequence)
    return bits

def main():
    fs = 2_000_000
    archivos = [
        
      'muestras/muestrasTfg/muestraAX0.complex16s',
      'muestras/muestrasTfg/muestraBX0.complex16s',
      'muestras/muestrasTfg/muestraCX1.complex16s',
      'muestras/muestrasTfg/muestraDX0.complex16s',

    #    'muestras/muestrasTfg/muestraAX1.complex16s',
    #    'muestras/muestrasTfg/muestraAX2.complex16s',
    #    'muestras/muestrasTfg/muestraAX3.complex16s',
#
    #    'muestras/muestrasTfg/muestraAY0.complex16s',
    #    'muestras/muestrasTfg/muestraAY1.complex16s',
    #    'muestras/muestrasTfg/muestraAY2.complex16s',
    #    'muestras/muestrasTfg/muestraAY3.complex16s',
       
    #    'muestras/muestrasTfg/muestraAZ0.complex16s',
    #    'muestras/muestrasTfg/muestraAZ1.complex16s',
    #    'muestras/muestrasTfg/muestraAZ2.complex16s',
    #    'muestras/muestrasTfg/muestraAZ3.complex16s',

#        'muestras/muestrasTfg/not_working.complex16s',


        #'muestras/muestrasTfg/muestraAY1.complex16s'
    ]

    matriz_bits = []

    for archivo in archivos:
        try:
            bits = procesar_archivo(archivo, fs, plot_envolvente=DEBUG, plot_windows=DEBUG)
            matriz_bits.extend(bits)
            print(matriz_bits)
            # Guardar bits fila por fila para evitar errores con longitud variable
            with open(f'{archivo}.txt', 'w') as f:
                for fila in bits:
                    f.write(' '.join(map(str, fila)) + '\n')
            print(f'{archivo}: {bits}')
        except Exception as e:
            print(f"Error procesando {archivo}: {e}")

    if matriz_bits:
        max_len = max(len(fila) for fila in matriz_bits)
        matriz_array = np.full((len(matriz_bits), max_len), -1)
        for i, fila in enumerate(matriz_bits):
            matriz_array[i, :len(fila)] = fila

        df = pd.DataFrame(matriz_array)
        plt.figure(figsize=(12, 8))
        sns.heatmap(df, annot=True, fmt='d', cmap='viridis', cbar=True, linewidths=0.5, linecolor='gray')
        plt.xlabel("Índice de bit")
        plt.ylabel("Paquete (fila)")
        plt.title("Bits detectados en formato tabla")
        plt.show()


    else:
        print("No se detectaron bits en ningún archivo.")

if __name__ == "__main__":
    main()

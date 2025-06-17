import numpy as np
from scipy.signal import hilbert, welch
import matplotlib.pyplot as plt

def calculate_carrier_frequency(filename, fs=2_000_000, plot_spectrum=False):
    """
    Calculate the carrier frequency from a complex signal file.
    
    Args:
        filename: Path to the complex signal file (.complex16s)
        fs: Sampling frequency (default 2 MHz)
        plot_spectrum: Whether to plot the power spectrum (for debugging)
    
    Returns:
        The detected carrier frequency in Hz, or None if no clear carrier is found
    """
    # Load the complex signal
    yt = np.fromfile(filename, dtype=np.int8)
    I = yt[0::2]
    Q = yt[1::2]
    complex_signal = I + 1j*Q
    
    # Compute power spectral density using Welch's method
    f, Pxx = welch(complex_signal, fs=fs, nperseg=min(1024, len(complex_signal)), 
                  return_onesided=False)
    
    # Shift frequencies to center around 0
    f = np.fft.fftshift(f)
    Pxx = np.fft.fftshift(Pxx)
    
    # Find the peak frequency (potential carrier)
    peak_idx = np.argmax(Pxx)
    carrier_freq = abs(f[peak_idx])
    
    # Optional plotting for debugging
    if plot_spectrum:
        plt.figure(figsize=(10, 5))
        plt.plot(f, 10*np.log10(Pxx))
        plt.axvline(carrier_freq, color='r', linestyle='--', label=f'Detected: {carrier_freq/1000:.1f} kHz')
        plt.axvline(-carrier_freq, color='r', linestyle='--')
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Power Spectral Density (dB/Hz)')
        plt.title('Power Spectrum with Detected Carrier Frequency')
        plt.legend()
        plt.grid()
        plt.show()
    
    # Only return frequencies with significant power
    if Pxx[peak_idx] > np.mean(Pxx) * 10:  # At least 10x higher than average
        return carrier_freq
    else:
        return None

if __name__ == "__main__":
    # Example usage
    filename = 'muestras/muestrasTfg/muestraAX0.complex16s'  # Replace with your file path
    
    carrier_freq = calculate_carrier_frequency(filename)
    if carrier_freq is not None:
        print(f"Detected carrier frequency: {carrier_freq:.2f} Hz ({carrier_freq/1000:.2f} kHz)")
    else:
        print("No clear carrier frequency detected in the signal.")

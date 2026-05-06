from parselmouth import praat
from helper import get_avg_formant_bandwidth, calc_iseli_correction

"""
Here we call both functions for spectral tilt (H1-H2 and H1-A3) 
"""

def extract_h1_h2_function(pitch_obj, sound, timestamps, f1, f2, formant_obj):

    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    v_obj = sound.extract_part(start, end, preserve_times=True)
    h1_freq = praat.call(pitch_obj, "Get mean", start, end, "Hertz")
    h2_freq = h1_freq * 2
    h1_bw = (h1_freq / 5)
    h2_bw = h1_bw
    # Get spectrum and ltas objects
    spec_obj = v_obj.to_spectrum()
    ltas_obj = praat.call(spec_obj, "To Ltas (1-to-1)")
    # Extract dB values for h1 and h2
    h1_db = praat.call(ltas_obj, "Get maximum", h1_freq-h1_bw/2, h1_freq+h2_bw/2, "none")
    h2_db = praat.call(ltas_obj, "Get maximum", h2_freq-h1_bw/2, h2_freq+h2_bw/2, "none")
    # Get first formant and bandwidth of formant for correction
    f1_bw = get_avg_formant_bandwidth(1, formant_obj, start, end)               
    # Get second formant and bandwidth of formant for correction
    f2_bw = get_avg_formant_bandwidth(2, formant_obj, start, end)
    # Get corrected values
    sample_rate = praat.call(sound, "Get sampling frequency")
    h1_db_c = h1_db - calc_iseli_correction(h1_freq, f1, f1_bw, sample_rate) - calc_iseli_correction(h1_freq, f2, f2_bw, sample_rate)
    h2_db_c = h2_db - calc_iseli_correction(h2_freq, f1, f1_bw, sample_rate) - calc_iseli_correction(h2_freq, f2, f2_bw, sample_rate)
    h1_h2 = h1_db_c - h2_db_c
    return h1_h2, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c


def extract_h1_a3_function(timestamps, formant_obj, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c):
    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    f1 = praat.call(formant_obj, "Get mean", 1, start, end, "Hertz")
    f2 = praat.call(formant_obj, "Get mean", 2, start, end, "Hertz")
    f3 = praat.call(formant_obj, "Get mean", 3, start, end, "Hertz")
    f3_bw = get_avg_formant_bandwidth(3, formant_obj, start, end)
    a3_db = praat.call(ltas_obj, "Get maximum", f3*0.9, f3*1.1, "none")
    a3_freq = praat.call(ltas_obj, "Get frequency of maximum", f3*0.9, f3*1.1, "none")
    a3_db_c = a3_db - calc_iseli_correction(a3_freq, f1, f1_bw, sample_rate) - calc_iseli_correction(a3_freq, f2, f2_bw, sample_rate) - calc_iseli_correction(a3_freq, f3, f3_bw, sample_rate)
    h1_a3 = h1_db_c - a3_db_c
    return h1_a3               



from parselmouth import praat

def extract_CPPS_function(sound, timestamps):
    
    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    v_obj = sound.extract_part(start, end, preserve_times=True)

    
    cepst = praat.call(v_obj, "To PowerCepstrogram", 60, 0.002, 5000, 50)
    cpps = praat.call(cepst, "Get CPPS","yes", 0.02, 0.0005, 60, 330, 0.05, "parabolic", 0.001, 0.05, "Exponential decay", "Robust slow") 
    return cpps

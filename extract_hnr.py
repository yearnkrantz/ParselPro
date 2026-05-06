from parselmouth import praat

def extract_hnr_function(pitch_obj, sound, timestamps):
    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    v_obj = sound.extract_part(start, end, preserve_times=True)
    min_f0 = praat.call(pitch_obj, "Get minimum", start, end, "Hertz", "parabolic")
    min_f0 = min_f0 - 2
    end = v_obj.get_end_time()
    harmonics = praat.call(v_obj, "To Harmonicity (cc)", 0.01, min_f0, 0.1, 1.0)
    hnr = praat.call(harmonics, "Get mean...", 0, end)
    return hnr

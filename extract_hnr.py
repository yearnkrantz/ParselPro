from parselmouth import praat
from helper import get_gender

def extract_hnr_function(sound, timestamps, metadata):
    gender = get_gender(metadata)
    if gender == "m":
        pitch_floor = 60
        pitch_ceiling = 300
    else:
        pitch_floor = 100
        pitch_ceiling = 500
    pitch_obj = sound.to_pitch_cc(pitch_floor = pitch_floor, pitch_ceiling = pitch_ceiling)



    start = timestamps[0]["start"]
    end = timestamps[0]["end"]
    v_obj = sound.extract_part(start, end, preserve_times=True)
    min_f0 = praat.call(pitch_obj, "Get minimum", start, end, "Hertz", "parabolic")
    min_f0 = min_f0 - 2

    end = v_obj.get_end_time()
    harmonics = praat.call(v_obj, "To Harmonicity (cc)", 0.01, min_f0, 0.1, 1.0)
    hnr = praat.call(harmonics, "Get mean...", 0, end)
    
    return hnr

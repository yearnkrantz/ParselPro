from parselmouth import praat
from helper import get_gender

def extract_formants_function(sound, timestamps, metadata):


    # Look up the gender for that speaker
    gender = get_gender(metadata)


    # Set max_formant depending on gender
    max_formant = 4500.0 if gender == "m" else 5500.0
    formant_obj = sound.to_formant_burg(maximum_formant=max_formant)
    if gender == "m":
        pitch_floor = 60
        pitch_ceiling = 300
    else:
        pitch_floor = 100
        pitch_ceiling = 500
    pitch_obj = sound.to_pitch_cc(pitch_floor = pitch_floor, pitch_ceiling = pitch_ceiling)
    #pitch_obj = sound.to_pitch()

    #getting filtered autocorr to work would be the next goal, but just for F0
    #pitch_obj = praat.call(sound, "To Pitch (filtered autocorrelation)", 0.001, 50, 800, 15, "no", 0.5, 0.09, 0.5, 0.055, 0.35, 0.14)


    start = timestamps[0]["start"]
    end = timestamps[0]["end"]

    f1 = praat.call(formant_obj, "Get mean", 1, start, end, "Hertz")
    f2 = praat.call(formant_obj, "Get mean", 2, start, end, "Hertz")
    f3 = praat.call(formant_obj, "Get mean", 3, start, end, "Hertz")
    mean_pitch = praat.call(pitch_obj, "Get mean", start, end, "Hertz")
    min_pitch = praat.call(pitch_obj, "Get minimum", start, end, "Hertz", "Parabolic")
    max_pitch = praat.call(pitch_obj, "Get maximum", start, end, "Hertz", "Parabolic")

    return f1, f2, f3, mean_pitch, min_pitch, max_pitch, formant_obj, max_formant
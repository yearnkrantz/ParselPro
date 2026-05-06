from parselmouth import praat
from helper import get_gender

def extract_shimmer_function(sound, timestamps, metadata):
    gender = get_gender(metadata)
    
    if gender == "m":
        pitch_floor, pitch_ceiling = 60, 300
    else:
        pitch_floor, pitch_ceiling = 100, 500
    pitch_obj = sound.to_pitch_cc(pitch_floor = pitch_floor, pitch_ceiling = pitch_ceiling)


    start = timestamps[0]["start"]
    end = timestamps[0]["end"]
    v_obj = sound.extract_part(start, end, preserve_times=True)

    min_f0 = float(praat.call(pitch_obj, "Get minimum", start, end, "Hertz", "parabolic"))
    max_f0 = float(praat.call(pitch_obj, "Get maximum", start, end, "Hertz", "parabolic"))


    pointprocess = praat.call(v_obj, "To PointProcess (periodic, cc)", min_f0, max_f0)

    shortest_period = 1.0 / max_f0
    longest_period  = 1.0 / min_f0


    shimmer = praat.call(
    [pointprocess, sound], 
    "Get shimmer (local)", 0.0, 0.0, shortest_period, longest_period, 1.3, 1.6
    )

    shimmer_percent = shimmer * 100

    return shimmer_percent
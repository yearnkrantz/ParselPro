from parselmouth import praat

def extract_shimmer_function(pitch_obj, sound, timestamps):

    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
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
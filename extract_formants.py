from parselmouth import praat
import parselmouth
from helper import get_gender
import json
from pathlib import Path

def extract_formants_function(sound, timestamps, metadata, filename_base=None, key_col="Audiofile"):


    # Look up the gender for that speaker
    gender = get_gender(metadata, filename_base=filename_base, key_col=key_col)


    # Set max_formant depending on gender
    max_formant = 4500.0 if gender == "m" else 5500.0
    formant_obj = sound.to_formant_burg(maximum_formant=max_formant)
    if gender == "m":
        pitch_floor = 60
        pitch_ceiling = 300
    else:
        pitch_floor = 100
        pitch_ceiling = 500
    
    # Load config to check if we should use a separate pitch object
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    use_separate_pitch_object = config.get("toggles", {}).get("use_separate_pitch_object", False)
    
    if use_separate_pitch_object and filename_base:
        # Load pitch object from the specified path
        pitch_object_path = Path(config.get("pitch_object_path", ""))
        pitch_file = pitch_object_path / f"{filename_base}.Pitch"
        
        if pitch_file.exists():
            pitch_obj = parselmouth.read(str(pitch_file))
        else:
            # Fallback to computing pitch if file not found
            print(f"Warning: Pitch object file not found at {pitch_file}, computing pitch instead")
            pitch_obj = sound.to_pitch_cc(pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling)
    else:
        # Use the original method: compute pitch from sound
        pitch_obj = sound.to_pitch_cc(pitch_floor = pitch_floor, pitch_ceiling = pitch_ceiling)
    #pitch_obj = sound.to_pitch()

    #getting filtered autocorr to work would be the next goal, but just for F0
    #pitch_obj = praat.call(sound, "To Pitch (filtered autocorrelation)", 0.001, 50, 800, 15, "no", 0.5, 0.09, 0.5, 0.055, 0.35, 0.14)


    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]

    f1 = praat.call(formant_obj, "Get mean", 1, start, end, "Hertz")
    f2 = praat.call(formant_obj, "Get mean", 2, start, end, "Hertz")
    f3 = praat.call(formant_obj, "Get mean", 3, start, end, "Hertz")
    mean_pitch = praat.call(pitch_obj, "Get mean", start, end, "Hertz")
    min_pitch = praat.call(pitch_obj, "Get minimum", start, end, "Hertz", "Parabolic")
    max_pitch = praat.call(pitch_obj, "Get maximum", start, end, "Hertz", "Parabolic")
    mean_pitch_cross_utterance = praat.call(pitch_obj, "Get mean", 0.0, 0.0, "Hertz")

    return pitch_obj, f1, f2, f3, mean_pitch, mean_pitch_cross_utterance, min_pitch, max_pitch, formant_obj, max_formant
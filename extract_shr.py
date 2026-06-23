
import os
import sys
import numpy as np
import parselmouth
import subprocess
from parselmouth import praat

# Download opensauce-python from GitHub if not already in CWD
if not os.path.exists('opensauce-python'):
   subprocess.call(['git', 'clone', 'https://github.com/voicesauce/opensauce-python.git'])

# # Import the shrp function from opensauce
opensauce_path = os.path.abspath("./opensauce-python")
sys.path.insert(0, opensauce_path)
from opensauce import shrp

# Two settings for SHR Algorithm
# 1. SHR Adaptive:
# - min_f0_shr = 0.4 min_pitch
# - ceiling_shr = 5 * max pitch (< 22100 due to Nyquist)
# - frame_length_shr = 5000 / min_pitch

# 2. SHR Adaptive 2:
# - min_f0_shr = 0.4 min_pitch
# - ceiling_shr = 6 * max pitch (< 22100 due to Nyquist)
# - frame_length_shr = 10000 / min_pitch

def extract_shr_function(sound, pitch_obj, timestamps):
    # Load sound and extract pitch
    #sound = parselmouth.Sound(sound_path)
    #pitch = sound.to_pitch(
    #    time_step=0.01,
    #    pitch_floor=pitch_floor,
    #    pitch_ceiling=pitch_ceiling
    #)

    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    s_obj = sound.extract_part(start, end, preserve_times=True)
    # shrp() takes 1D NumPy array
    y = s_obj.values
    if y.ndim == 2:
            if y.shape[0] == 1:
                y = y[0]
            else:
                y = y.mean(axis=0)
    y = np.asarray(y, dtype=float)
    fs = s_obj.sampling_frequency

    # Calculate the 5th and 95th percentile of pitch values for SHR parameter calculation
    # Just to be conservative and remove outliers
    fifth_percentile_pitch = praat.call(pitch_obj, "Get quantile", start, end, 0.05, "Hertz")
    nintyfifth_percentile_pitch = praat.call(pitch_obj, "Get quantile", start, end, 0.95, "Hertz")

    # Adaptive SHR parameters based on pitch percentiles
    # SHR Adaptive 2
    min_f0_shr = 0.4 * fifth_percentile_pitch
    max_f0_shr = nintyfifth_percentile_pitch
    ceiling_shr = min(6 * nintyfifth_percentile_pitch, (fs / 2) - 1)
    frame_length_shr = 10000 / fifth_percentile_pitch

    f0_time_ms, f0_value, shr_value, f0_candidates = shrp.shrp(
        Y=y, # Input data (1D NumPy array)
        Fs=int(fs), # Sampling frequency
        F0MinMax=[min_f0_shr, max_f0_shr], # F0 range for pitch estimation
        frame_length=frame_length_shr, # Frame length in ms
        timestep=5, # Intervals timestep; 5 is chosen in Herbst
        SHR_Threshold=0.01, #If the estimated SHR is greater than the threshold, the subharmonic is regarded as F0 candidate. Otherwise, the harmonic is favored.
        ceiling=ceiling_shr, # Upper bound of frequencies for pitch estimation
        med_smooth=0, # No median smoothing
        CHECK_VOICING=0 # Not implemented in opensauce-python, set to 0
    )

    return f0_time_ms, f0_value, shr_value, f0_candidates
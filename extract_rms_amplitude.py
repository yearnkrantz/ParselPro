
def extract_rms_function(sound, timestamps):
    
    # Get segment duration and RMS
    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    rms = sound.get_root_mean_square(from_time=start, to_time=end)
    return rms
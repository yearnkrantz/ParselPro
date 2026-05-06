import numpy as np



def extract_shr_function(sound, timestamps, formant_obj, max_formant, time_step=0.01):
    """
    Compute Sun (2002) SHR over [start, end] by calculating SHR per frame.
    
    sound       : Parselmouth Sound object
    start, end  : analysis window
    time_step   : frame step in seconds (e.g. 0.01 = 10 ms)
    max_formant : Praat formant ceiling
    
    Returns mean SHR across frames
    """

    #get timestamps
    start = timestamps[0]["seg_start"]
    end = timestamps[0]["seg_end"]
    # get formant object
    formant_obj = sound.to_formant_burg(maximum_formant=max_formant)
    shr_values = []

    # iterate over frames
    t = start
    while t <= end:
        f1 = formant_obj.get_value_at_time(1, t)  # F1 at time t
        f2 = formant_obj.get_value_at_time(2, t)  # F2 at time t

        if f1 and f2 and f1 > 0 and f2 > 0:
            # get amplitude spectrum at that frame
            frame_sound = sound.extract_part(from_time=t-0.005, to_time=t+0.005, preserve_times=True)  # 10 ms slice
            spectrum = frame_sound.to_spectrum()
            
            # getting linear amplitude for f1
            bin_floatf1 = spectrum.get_bin_number_from_frequency(f1)
            bin_indexf1 = round(bin_floatf1)
            binvalf1 = spectrum.get_value_in_bin(bin_indexf1)
            lin_amp_f1= abs(binvalf1)

            # getting linear amplitude for f2
            bin_floatf2 = spectrum.get_bin_number_from_frequency(f2)
            bin_indexf2 = round(bin_floatf2)
            binvalf2 = spectrum.get_value_in_bin(bin_indexf2)
            lin_amp_f2= abs(binvalf2)

            if lin_amp_f1 + lin_amp_f2 > 0:
                shr = 0.5 * ((lin_amp_f1 - lin_amp_f2) / (lin_amp_f1 + lin_amp_f2))
                shr_values.append(shr)

        t += time_step

    if len(shr_values) == 0:
        return float("nan")

    return (np.mean(shr_values)) * 100




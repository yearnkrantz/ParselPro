import chardet
import tgt
from parselmouth import praat
import math
import codecs
#---#

def detect_encoding_function(textgrid_file, read_bytes=20000):
    """Try to detect encoding robustly using BOM check, chardet."""
    with open(textgrid_file, "rb") as fh:
        raw = fh.read(read_bytes)

    # BOM-based quick checks
    if raw.startswith(codecs.BOM_UTF8):
        return "utf-8-sig"
    if raw.startswith(codecs.BOM_UTF16_LE):
        return "utf-16"
    if raw.startswith(codecs.BOM_UTF16_BE):
        return "utf-16"
    # chardet fallback (may be None)
    ch = chardet.detect(raw)
    if ch and ch.get("encoding"):
        return ch["encoding"]

#---#

def extract_timestamps_function(input_dir, textgrid_file, vowel_tier, target_vowel):

    timestamps = []
    file_encoding = detect_encoding_function(textgrid_file)  
    textgrid_path_file = input_dir / textgrid_file.name  

    try:
        textgrid = tgt.io.read_textgrid(
            textgrid_path_file, 
            encoding=file_encoding, 
            include_empty_intervals=False
        )
    except Exception as e:
        print(f"ERROR: Failed to read {textgrid_file.name} with encoding {file_encoding}: {e}")
        return []

    if vowel_tier not in [tier.name for tier in textgrid.tiers]:
        print(f"WARNING: Tier '{vowel_tier}' not found in {textgrid_file.name}")
        return []

    syll_data = textgrid.get_tier_by_name(vowel_tier)

    for interval in syll_data.intervals:
        interval_vowel = interval.text.strip().lower()
        if interval_vowel in [v.lower() for v in target_vowel]:    
            entry = {
                "start": interval.start_time,
                "end": interval.end_time,
                "duration": interval.end_time - interval.start_time
            }
            timestamps.append(entry)

    return timestamps


#---#

def get_avg_formant_bandwidth(f_nr, f_obj, start, end):
    sum = 0
    dur = end - start
    s = 10
    for i in range(0, s):
        timept = start + dur * i/10
        bw_i = praat.call(f_obj, "Get bandwidth at time", f_nr, timept, "hertz", "linear")
        sum = sum + bw_i
    avg_bw = sum / s
    return avg_bw

#---#

def calc_iseli_correction(hx, fx, bx, fs):
    r = math.exp(-math.pi * bx / fs)
    omega_fx = 2 * math.pi * fx / fs
    omega_hx = 2 * math.pi * hx / fs
    numerator = (1 - 2 * r * math.cos(omega_fx) + r**2)**2
    denom1 = (1 - 2 * r * math.cos(omega_fx + omega_hx) + r**2)
    denom2 = (1 - 2 * r * math.cos(omega_fx - omega_hx) + r**2)
    corr = 10 * math.log10( numerator / ( denom1 * denom2 ) )
    return corr

#---#

def db_to_lin_amp(db):
    return 10 ** (db / 20.0) if db != -math.inf else 0.0

#---#

def get_gender(metadata):
    speaker_name = metadata.get("Filename", None)

    # Look up the sex for that speaker
    row = metadata.loc[metadata["Filename"] == speaker_name, "Sex"]

    if not row.empty:
        gender = row.iloc[0]
    else:
        gender = "f"  # default
    return gender

#---#
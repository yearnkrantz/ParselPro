import chardet
import pandas as pd
import tgt
from parselmouth import praat
import math
import codecs
import unicodedata
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

def extract_timestamps_function(input_dir, textgrid_file, segment_tier, target_vowel, syll_tier=None, first_only=False):

    """Extract timestamps from segment and syllable tiers in a TextGrid.

    - Handles both IntervalTier (uses interval.start_time/end_time) and PointTier (creates a small window around the point).
    - target_vowel may be a string or a list of strings; matching is case-insensitive exact match after strip().
    - If syll_tier is provided, also extracts syllable boundaries that align with segment timestamps.
    - If first_only is True, returns as soon as the first matching item is found.
    """

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

    # Match tier names case-insensitively and strip whitespace
    tier_names = [tier.name for tier in textgrid.tiers]
    lower_to_tier = {tier.name.strip().lower(): tier for tier in textgrid.tiers}
    
    # Get segment tier
    requested_seg = segment_tier.strip().lower()
    if requested_seg in lower_to_tier:
        segment_data = lower_to_tier[requested_seg]
    else:
        print(f"WARNING: Tier '{segment_tier}' not found in {textgrid_file.name}. Available tiers: {tier_names}")
        return []
    
    # Get syllable tier if provided
    syllable_data = None
    if syll_tier:
        requested_syll = syll_tier.strip().lower()
        if requested_syll in lower_to_tier:
            syllable_data = lower_to_tier[requested_syll]
        else:
            print(f"WARNING: Syllable tier '{syll_tier}' not found in {textgrid_file.name}")

    # Normalize targets to a lower-case set for fast membership tests (unicode-normalized)
    def _norm(s):
        return unicodedata.normalize("NFC", str(s).strip()).lower()

    if isinstance(target_vowel, (list, tuple)):
        target_set = {_norm(t) for t in target_vowel}
    else:
        target_set = {_norm(target_vowel)}

    # If it's an interval-tier, iterate intervals
    if hasattr(segment_data, 'intervals'):
        for interval in segment_data.intervals:
            interval_label = _norm(interval.text or "")
            # debug print
            print(f"interval: {interval.start_time}-{interval.end_time} '{interval_label}'")
            if interval_label in target_set:
                entry = {
                    "seg_start": interval.start_time,
                    "seg_end": interval.end_time,
                    "seg_duration": interval.end_time - interval.start_time
                }
                
                # If syllable tier is available, find overlapping syllable boundaries
                if syllable_data and hasattr(syllable_data, 'intervals'):
                    for syll_interval in syllable_data.intervals:
                        # Check if syllable overlaps with segment
                        if syll_interval.start_time < interval.end_time and syll_interval.end_time > interval.start_time:
                            entry["syll_start"] = syll_interval.start_time
                            entry["syll_end"] = syll_interval.end_time
                            entry["syll_duration"] = syll_interval.end_time - syll_interval.start_time
                            break  # Take the first overlapping syllable
                
                timestamps.append(entry)
                if first_only:
                    return timestamps

    # If it's a point-tier, treat each point as a small interval (window)
    if hasattr(segment_data, 'points'):
        # default window half-width in seconds around the point
        window = 0.02
        for point in segment_data.points:
            mark = _norm(point.mark or "")
            # debug
            # print(f"point: {point.time} '{mark}'")
            if mark in target_set:
                start = max(0.0, point.time - window)
                end = point.time + window
                entry = {"seg_start": start, "seg_end": end, "seg_duration": end - start}
                
                # If syllable tier is available, find overlapping syllable boundaries
                if syllable_data and hasattr(syllable_data, 'intervals'):
                    for syll_interval in syllable_data.intervals:
                        # Check if syllable overlaps with point window
                        if syll_interval.start_time < end and syll_interval.end_time > start:
                            entry["syll_start"] = syll_interval.start_time
                            entry["syll_end"] = syll_interval.end_time
                            entry["syll_duration"] = syll_interval.end_time - syll_interval.start_time
                            break  # Take the first overlapping syllable
                
                timestamps.append(entry)
                if first_only:
                    return timestamps

    if not timestamps:
        # collect a short sample of labels for debugging
        labels = []
        if hasattr(segment_data, 'intervals'):
            for interval in segment_data.intervals[:20]:
                labels.append(_norm(interval.text or ""))
        if hasattr(segment_data, 'points') and not labels:
            for point in segment_data.points[:20]:
                labels.append(_norm(point.mark or ""))
        print(f"No matching intervals/points found in tier '{segment_tier}' for targets {target_set} in {textgrid_file.name}. Sample labels: {labels}")

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
    # Defensive: handle missing or variant sex column names
    speaker_name = metadata.get("Audiofile", None)
    # Find the sex column (case-insensitive)
    sex_col = None
    for col in metadata.columns:
        if str(col).strip().lower() in ["sex", "vp.sex"]:
            sex_col = col
            break
    if sex_col is None:
        print(f"WARNING: No 'Sex' column (Sex, VP.sex, etc.) found in metadata for {speaker_name}; defaulting to 'f'")
        return "f"
    row = metadata.loc[metadata["Audiofile"] == speaker_name, sex_col]
    if not row.empty:
        gender = row.iloc[0]
        if pd.isna(gender) or str(gender).strip() == "":
            print(f"WARNING: '{sex_col}' value missing for {speaker_name}; defaulting to 'f'")
            return "f"
        gender_str = str(gender).strip().lower()
        if gender_str in ["m", "male"]:
            return "m"
        elif gender_str in ["f", "female"]:
            return "f"
        else:
            print(f"WARNING: Unknown '{sex_col}' value '{gender}' for {speaker_name}; defaulting to 'f'")
            return "f"
    else:
        print(f"WARNING: No metadata row for {speaker_name}; defaulting to 'f'")
        return "f"

#---#
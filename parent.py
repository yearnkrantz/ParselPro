import parselmouth as pm
import numpy as np
from pathlib import Path
import pandas as pd
import os
import json


"""
To run the tool, you first need to make adjustments in the config file,
set paths to your input data and where you would like your output to go.
The variable "syll_tier" is used only to get the syllable duration.
The variable "segment_tier" is then used for timestamps and parameter extraction.
Created by Jörn Krantz
"""

# load in the config file
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Access config settings
input_dir = Path(config["input_dir"])
output_dir = Path(config["output_dir"])
metadata_path = Path(config["participant_metadata"])
output_file = config["output_file"]
syll_tier = config["tiers"]["syll_tier"]
tobi_tier = config["tiers"]["tobi_tier"]
prominence_tier = config["tiers"]["prominence_tier"]
vowel_tier = config["tiers"]["segment_tier"]
target_vowel = config["targets"]["target_segment"]
target_syll = config["targets"]["target_syll"]
# Optional flag: only take the first matching target vowel (read from toggles)
first_instance_only = config.get("toggles", {}).get("first_instance_only", False)
#target_accent = config["targets"]["target_accent"]
toggles = config["toggles"]

#get functions from child scripts
from get_metadata import get_metadata_function
from helper import detect_encoding_function
from helper import extract_timestamps_function
from extract_formants import extract_formants_function
from extract_rms_amplitude import extract_rms_function
from extract_hnr import extract_hnr_function
from extract_jitter import extract_jitter_function
from extract_shimmer import extract_shimmer_function
from extract_spectral_tilt import extract_h1_h2_function
from extract_spectral_tilt import extract_h1_a3_function
from extract_shr import extract_shr_function
from extract_CPPS import extract_CPPS_function


# Store problems for later inspection
errors = []

print(f"Using vowel_tier='{vowel_tier}', target_vowel={target_vowel}, first_instance_only={first_instance_only}")

# --- Load and normalize metadata ---
# If the metadata path is an Excel file, use read_excel; otherwise try encoding detection and csv fallbacks
metadata = None
errors_read = []
suffix = str(metadata_path).lower()
if suffix.endswith(('.xls', '.xlsx')):
    try:
        metadata = pd.read_excel(metadata_path)
        print(f"Read metadata as Excel: {metadata_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to read metadata Excel {metadata_path}: {e}")
else:
    # Try to detect encoding for the metadata CSV and fall back to common encodings
    try:
        metadata_encoding = detect_encoding_function(metadata_path, read_bytes=20000)
    except Exception:
        metadata_encoding = None

    if metadata_encoding:
        try:
            metadata = pd.read_csv(metadata_path, encoding=metadata_encoding)
            print(f"Read metadata with detected encoding: {metadata_encoding}")
        except Exception as e:
            errors_read.append((metadata_encoding, str(e)))

    if metadata is None:
        # Try common encodings typically used on Windows (cp1252) and a safe fallback (latin-1)
        for enc in ("utf-8", "cp1252", "latin-1"):
            try:
                metadata = pd.read_csv(metadata_path, encoding=enc)
                print(f"Read metadata with fallback encoding: {enc}")
                metadata_encoding = enc
                break
            except Exception as e:
                errors_read.append((enc, str(e)))

    if metadata is None:
        raise RuntimeError(f"Failed to read metadata CSV {metadata_path}. Attempts: {errors_read}")

# Normalize and detect the primary file-id column (Audiofile or Filename)
possible_keys = [k for k in ("Audiofile", "Filename") if k in metadata.columns]
if not possible_keys:
    raise RuntimeError(f"Metadata file must contain one of 'Audiofile' or 'Filename' columns. Found: {list(metadata.columns)}")
key_name = possible_keys[0]
metadata[key_name] = metadata[key_name].astype(str).str.strip()#.str.lower()

# Prepare containers
results = pd.DataFrame()
input_dir = Path(input_dir)
output_dir = Path(output_dir)

# --- Processing loop ---
for idx, row in metadata.iterrows():
    filename_base = str(row[key_name]).strip()#.lower()

    audio_file = input_dir / f"{filename_base}.wav"
    if not audio_file.exists():
        errors.append((filename_base, "Missing audio file"))
        continue

    try:
        sound = pm.Sound(str(audio_file))
    except Exception as e:
        errors.append((filename_base, f"Failed to read audio: {e}"))
        continue

    textgrid_file = audio_file.with_suffix(".TextGrid")
    if not textgrid_file.exists():
        errors.append((filename_base, "Missing TextGrid file"))
        continue

    # Metadata extraction
    if config["toggles"]["get_metadata"]:
        try:
            _ = get_metadata_function(textgrid_file)  # placeholder if you actually need metadata from it
        except Exception as e:
            errors.append((filename_base, f"Metadata extraction failed: {e}"))
            continue

    # Encoding detection
    try:
        encoding = detect_encoding_function(textgrid_file, read_bytes=20000)
    except Exception as e:
        errors.append((filename_base, f"Encoding detection failed: {e}"))
        continue

    # Timestamps extraction
    try:
        timestamps = extract_timestamps_function(input_dir, textgrid_file, vowel_tier, target_vowel, syll_tier=syll_tier, first_only=first_instance_only)
        print(f"{filename_base}: extracted {len(timestamps)} timestamp(s)")
    except Exception as e:
        errors.append((filename_base, f"Timestamps extraction failed: {e}"))
        continue

    if not timestamps:
        # No matching intervals/points were found for this file — log and skip
        errors.append((filename_base, "No timestamps extracted (no matching targets in tier)"))
        continue

    # Formants
    try:
        pitch_obj, f1, f2, f3, mean_pitch, mean_pitch_cross_utterance, min_pitch, max_pitch, formant_obj, max_formant = extract_formants_function(sound, timestamps, metadata, filename_base)
    except Exception as e:
        errors.append((filename_base, f"Formant extraction failed: {e}"))
        continue


    # Optional features
    try:
        rms = extract_rms_function(sound, timestamps) if config["toggles"]["extract_rms_amplitude"] else None
    except Exception as e:
        errors.append((filename_base, f"Amplitude extraction failed: {e}"))
        continue

   
    try:
        hnr = extract_hnr_function(pitch_obj, sound, timestamps) if config["toggles"]["extract_HNR"] else None
        jitter = extract_jitter_function(pitch_obj, sound, timestamps) if config["toggles"]["extract_Jitter"] else None
        shimmer = extract_shimmer_function(pitch_obj, sound, timestamps) if config["toggles"]["extract_Shimmer"] else None
        h1_h2 = None
        h1_a3 = None
        # We'll compute a single mean SHR value per file (scalar) rather than storing the whole frame-wise array.
        shr_mean = None
        # initialize these in case callers expect them later
        f0_time_ms = None
        f0_value = None
        shr_value = None
        f0_candidates = None
        if config["toggles"]["extract_H1_H2"]:
            h1_h2, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c = extract_h1_h2_function(
                pitch_obj, sound, timestamps, f1, f2, formant_obj
            )
        if config["toggles"]["extract_H1_A3"]:
            h1_a3 = extract_h1_a3_function(
                timestamps, formant_obj, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c
            )
        if config["toggles"]["extract_SHR"]:
            f0_time_ms, f0_value, shr_value, f0_candidates = extract_shr_function(sound, pitch_obj, timestamps)
            # shr_value is typically a 1D array (frame-wise SHR). Compute its mean; if empty, set to NaN.
            try:
                arr = np.asarray(shr_value, dtype=float)
                if arr.size == 0:
                    shr_mean = float('nan')
                else:
                    shr_mean = float(np.nanmean(arr))
            except Exception:
                # If conversion fails, store NaN so downstream code can handle missing values
                shr_mean = float('nan')
        if config["toggles"]["extract_CPPS"]:
            cpps = extract_CPPS_function(sound, timestamps)
        else:
            cpps = None
    except Exception as e:
        errors.append((filename_base, f"Feature extraction failed: {e}"))
        continue

    # Collect results for this file (include interval start/end for audit)
    parameter_list = pd.DataFrame({
        key_name: [filename_base],
        "segment_start": [timestamps[0]["seg_start"]],
        "segment_end": [timestamps[0]["seg_end"]],
        "syllable_start": [timestamps[0]["syll_start"]],
        "syllable_end": [timestamps[0]["syll_end"]],
        "segment_duration": [timestamps[0]["seg_duration"]],
        "syllable_duration": [timestamps[0]["syll_duration"]],
        "F1_mean": [f1],
        "F2_mean": [f2],
        "F3_mean": [f3],
        "mean_pitch": [mean_pitch],
        "mean_pitch_across_utterance": [mean_pitch_cross_utterance],
        "min_pitch": [min_pitch],
        "max_pitch": [max_pitch],
        "rms_amplitude": [rms],
        "hnr": [hnr if config["toggles"]["extract_HNR"] else None],
        "jitter": [jitter if config["toggles"]["extract_Jitter"] else None],
        "shimmer": [shimmer if config["toggles"]["extract_Shimmer"] else None],
        "h1_h2": [h1_h2 if config["toggles"]["extract_H1_H2"] else None],
        "h1_a3": [h1_a3 if config["toggles"]["extract_H1_A3"] else None],
        "shr": [shr_mean if config["toggles"]["extract_SHR"] else None],
        "CPPS": [cpps]
    })

    results = pd.concat([results, parameter_list], ignore_index=True)

# --- Merge results with metadata ---

output_path = output_dir / output_file

# Always start from the full metadata as the master frame
if os.path.exists(output_path):
    master_data = pd.read_excel(output_path)
else:
    master_data = metadata.copy()

print(results.head())
print(results.columns)

# --- Merge this run’s results into the master frame ---
# We'll merge on the detected key_name (e.g., 'Audiofile' or 'Filename').
merge_key = key_name

# Ensure the results DataFrame contains the merge key (even if empty) so merge won't fail
if merge_key not in results.columns:
    # create an empty column with the same dtype as master_data[merge_key] when possible
    try:
        results[merge_key] = pd.Series(dtype=master_data[merge_key].dtype)
    except Exception:
        results[merge_key] = pd.Series(dtype=object)

merged = master_data.merge(results, on=merge_key, how="left", suffixes=("", "_new"))

# Update only the result columns (skip the merge key)
for col in results.columns:
    if col != merge_key:
        new_col = f"{col}_new"
        if new_col in merged.columns:
            # Prefer new values where available
            merged[col] = merged[new_col].combine_first(merged[col])
            merged.drop(columns=[new_col], inplace=True)

master_data = merged

# Save back
master_data.to_excel(output_path, index=False)



# --- Report errors ---
if errors:
    print("\nSkipped or failed:")
    for fname, err in errors:
        print(f" - {fname}: {err}")

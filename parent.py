import parselmouth as pm
from pathlib import Path
import pandas as pd
import os
import json
import numpy as np



with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

# Access values
input_dir = Path(config["input_dir"])
output_dir = Path(config["output_dir"])
metadata_path = Path(config["participant_metadata"])
output_file = config["output_file"]
syll_tier = config["tiers"]["syll_tier"]
tobi_tier = config["tiers"]["tobi_tier"]
prominence_tier = config["tiers"]["prominence_tier"]
vowel_tier = config["tiers"]["vowel_tier"]
target_vowel = config["targets"]["target_vowel"]
target_syll = config["targets"]["target_syll"]
#target_accent = config["targets"]["target_accent"]
toggles = config["toggles"]


from get_metadata import get_metadata_function
from helper import detect_encoding_function
from helper import extract_timestamps_function
from extract_formants import extract_formants_function
from extract_hnr import extract_hnr_function
from extract_jitter import extract_jitter_function
from extract_shimmer import extract_shimmer_function
from extract_spectral_tilt import extract_h1_h2_function
from extract_spectral_tilt import extract_h1_a3_function
from extract_shr import extract_shr_function
from extract_CPPS import extract_CPPS_function


import pandas as pd
from pathlib import Path
import parselmouth as pm
import tgt

# Store problems for later inspection
errors = []

# --- Load and normalize metadata ---
metadata = pd.read_csv(metadata_path)
metadata["Filename"] = metadata["Filename"].astype(str).str.strip()#.str.lower()

# Prepare containers
results = pd.DataFrame()
input_dir = Path(input_dir)
output_dir = Path(output_dir)

# --- Processing loop ---
for idx, row in metadata.iterrows():
    filename_base = str(row["Filename"]).strip()#.lower()

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
        timestamps = extract_timestamps_function(input_dir, textgrid_file, vowel_tier, target_vowel)
    except Exception as e:
        errors.append((filename_base, f"Timestamps extraction failed: {e}"))
        continue

    if not timestamps:
        errors.append((filename_base, "No timestamps extracted"))
        continue

    # Formants
    try:
        f1, f2, f3, mean_pitch, min_pitch, max_pitch, formant_obj, max_formant = extract_formants_function(sound, timestamps, metadata)
    except Exception as e:
        errors.append((filename_base, f"Formant extraction failed: {e}"))
        continue

    # Optional features
    try:
        hnr = extract_hnr_function(sound, timestamps, metadata) if config["toggles"]["extract_HNR"] else None
        jitter = extract_jitter_function(sound, timestamps, metadata) if config["toggles"]["extract_Jitter"] else None
        shimmer = extract_shimmer_function(sound, timestamps, metadata) if config["toggles"]["extract_Shimmer"] else None
        h1_h2 = None
        h1_a3 = None
        shr = None
        if config["toggles"]["extract_H1_H2"]:
            h1_h2, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c = extract_h1_h2_function(
                sound, timestamps, f1, f2, formant_obj
            )
        if config["toggles"]["extract_H1_A3"]:
            h1_a3 = extract_h1_a3_function(
                timestamps, formant_obj, ltas_obj, f1_bw, f2_bw, sample_rate, h1_db_c
            )
        if config["toggles"]["extract_SHR"]:
            shr = extract_shr_function(sound, timestamps, formant_obj, max_formant)
        if config["toggles"]["extract_CPPS"]:
            cpps = extract_CPPS_function(sound, timestamps)
    except Exception as e:
        errors.append((filename_base, f"Feature extraction failed: {e}"))
        continue

    # Collect results for this file
    parameter_list = pd.DataFrame({
        "Filename": [filename_base],
        "start_time": [timestamps[0]["start"]],
        "end_time": [timestamps[0]["end"]],
        "duration": [timestamps[0]["duration"]],
        "F1_mean": [f1],
        "F2_mean": [f2],
        "F3_mean": [f3],
        "mean_pitch": [mean_pitch],
        "min_pitch": [min_pitch],
        "max_pitch": [max_pitch],
        "hnr": [hnr if config["toggles"]["extract_HNR"] else None],
        "jitter": [jitter if config["toggles"]["extract_Jitter"] else None],
        "shimmer": [shimmer if config["toggles"]["extract_Shimmer"] else None],
        "h1_h2": [h1_h2 if config["toggles"]["extract_H1_H2"] else None],
        "h1_a3": [h1_a3 if config["toggles"]["extract_H1_A3"] else None],
        "shr": [shr if config["toggles"]["extract_SHR"] else None],
        "CPPS": [cpps] if config["toggles"]["extract_CPPS"] else None
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
merged = master_data.merge(results, on="Filename", how="left", suffixes=("", "_new"))

# Update only the result columns
for col in results.columns:
    if col != "Filename":
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

# ParselPro — Acoustic & Spectral Parameter Extractor

ParselPro is a Python tool for batch extraction of acoustic and voice quality parameters from speech recordings. It is designed with phonetic researchers in mind: all settings are controlled through a single `config.json` file, no scripting knowledge is required to run it. Inspired by [ProsodyPro](http://www.homepages.ucl.ac.uk/~uclyyg01/webpage/prosodypro.html) (Xu, 2013), ParselPro combines the flexibility of Python with the measurement methods of Praat, accessed via [Parselmouth](https://parselmouth.readthedocs.io/).

---

## Features

ParselPro extracts the following parameters from a target segment defined by a Praat TextGrid tier:

| Parameter | Description |
|---|---|
| **F1, F2, F3** | Mean formant frequencies (Burg algorithm) |
| **F0** | Mean, min, and max pitch; cross-utterance mean (pitch_cc or pre-computed Pitch object) |
| **RMS Amplitude** | Root mean square amplitude of the target segment |
| **HNR** | Harmonics-to-noise ratio (cross-correlation method) |
| **Jitter** | Local period perturbation |
| **Shimmer** | Local amplitude perturbation |
| **H1–H2** | First spectral tilt measure (Iseli et al. correction applied) |
| **H1–A3** | Second spectral tilt measure (Iseli et al. correction applied) |
| **SHR** | Sub-harmonic ratio (SHRP algorithm via [opensauce-python](https://github.com/voicesauce/opensauce-python)) |
| **CPPS** | Cepstral peak prominence smoothed |

Each measure can be enabled or disabled independently via the `toggles` section in `config.json`. The gender of each speaker (read from the metadata file) is used to set appropriate formant and pitch ranges automatically.

---

## Requirements

```
parselmouth
pandas
openpyxl
tgt
chardet
numpy
```

Install dependencies via pip:

```bash
pip install parselmouth pandas openpyxl tgt chardet numpy
```

`opensauce-python` is cloned automatically from GitHub the first time SHR extraction is run.

---

## Input

ParselPro expects the following for each recording:

- A `.wav` audio file
- A Praat `.TextGrid` file with the same base name, in the same directory
- A **metadata file** (CSV or Excel) with at least:
  - A file-ID column named `Audiofile` or `Filename` (base name without extension)
  - A speaker sex column named `Sex` or `VP.sex` (values: `m`/`male` or `f`/`female`)

All files should be placed in the directory specified by `input_dir`.

---

## Configuration

All settings are controlled via `config.json`. A template is provided below — copy it, fill in your paths, and adjust tier/target names and toggles as needed.

```json
{
  "input_dir": "C:/path/to/your/audio_and_textgrid_files",
  "pitch_object_path": "C:/path/to/your/pitch_objects",
  "output_dir": "C:/path/to/your/output",
  "output_file": "results.xlsx",
  "participant_metadata": "C:/path/to/your/metadata.xlsx",

  "tiers": {
    "syll_tier": "target_syllable",
    "tobi_tier": "accent_annotation",
    "prominence_tier": "prominence_annotation",
    "segment_tier": "target_segment"
  },

  "targets": {
    "target_syll": ["ja", "nee"],
    "target_segment": ["aː", "eː"]
  },

  "toggles": {
    "get_metadata": false,
    "first_instance_only": true,
    "extract_formants": true,
    "use_separate_pitch_object": false,
    "extract_rms_amplitude": true,
    "extract_HNR": true,
    "extract_Jitter": true,
    "extract_Shimmer": true,
    "extract_H1_H2": true,
    "extract_H1_A3": true,
    "extract_SHR": true,
    "extract_CPPS": true
  }
}
```

### Key options

- **`segment_tier`** — the TextGrid tier containing the target segment labels. Can be an interval tier or a point tier.
- **`target_segment`** — one or more labels to match in the segment tier (case-insensitive, Unicode-normalized).
- **`first_instance_only`** — if `true`, only the first matching interval per file is used.
- **`use_separate_pitch_object`** — if `true`, loads a pre-computed Praat `.Pitch` file from `pitch_object_path` instead of computing pitch from the waveform. The Pitch file must share the base name of the audio file (e.g. `VP01_item01.Pitch`). Falls back to computing pitch if the file is not found.
- **`syll_tier`** — used to extract syllable boundaries that overlap with the target segment (for syllable duration output).

---

## Usage

1. Fill in `config.json` with your paths, tier names, and targets.
2. Run the script from the ParselPro directory:

```bash
python parent.py
```

3. Results are written to the Excel file specified in `output_file`. Each run merges new results into the existing output file if one already exists (files already present are updated, not duplicated).

Any files that could not be processed are listed in the console output at the end of the run.

---

## Output

The output Excel file contains the columns from your metadata file plus:

| Column | Description |
|---|---|
| `segment_start` / `segment_end` | Boundaries of the extracted segment (s) |
| `syllable_start` / `syllable_end` | Boundaries of the overlapping syllable (s) |
| `segment_duration` / `syllable_duration` | Durations (s) |
| `F1_mean`, `F2_mean`, `F3_mean` | Mean formant frequencies (Hz) |
| `mean_pitch` | Mean F0 within the segment (Hz) |
| `mean_pitch_across_utterance` | Mean F0 across the full recording (Hz) |
| `min_pitch`, `max_pitch` | Min/max F0 within the segment (Hz) |
| `rms_amplitude` | RMS amplitude |
| `hnr` | Harmonics-to-noise ratio (dB) |
| `jitter` | Local jitter |
| `shimmer` | Local shimmer |
| `h1_h2` | H1–H2 spectral tilt (dB, Iseli-corrected) |
| `h1_a3` | H1–A3 spectral tilt (dB, Iseli-corrected) |
| `shr` | Mean sub-harmonic ratio |
| `CPPS` | Cepstral peak prominence smoothed (dB) |

---

## Citation

If you use ParselPro in your research, please cite the following where applicable:

- **Parselmouth**: Jadoul, Y., Thompson, B., & de Boer, B. (2018). Introducing Parselmouth: A Python interface to Praat. *Journal of Phonetics*, 71, 1–15.
- **ProsodyPro** (inspiration): Xu, Y. (2013). ProsodyPro — A tool for large-scale systematic prosody research. *Proceedings of Tools and Resources for the Analysis of Speech Prosody*, 7–10.
- **opensauce-python** (SHR): [https://github.com/voicesauce/opensauce-python](https://github.com/voicesauce/opensauce-python)
- **Iseli correction**: Iseli, M., Shue, Y.-L., & Alwan, A. (2007). Age, sex, and vowel dependencies of acoustic measures related to the voice source. *JASA*, 121(4), 2283–2295.

---

*Created by Jörn Krantz*

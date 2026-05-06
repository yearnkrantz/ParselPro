import tgt
import os
import json

def load_config(config_path="config.json"):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_metadata_function(textgrid_file, metadata_list=None, config=None):
    # If metadata_list does not exist, create it
    if metadata_list is None:
        metadata_list = []
    if config is None:
        config = load_config()

    # Get the base filename without directory or extension
    base_name = os.path.splitext(os.path.basename(textgrid_file))[0]
    # Split by underscore
    parts = base_name.split('_')
    if len(parts) >= 2:
        speaker = parts[0]
        item = parts[1]
    # Get tier names from config
    # Example: config = {"tobi_tier": "Tobi", "syll_tier": "target_syll"}
    tobi_tier_name = config["tobi_tier"]
    syll_tier_name = config["syll_tier"]
    # Load the TextGrid file
    tg = tgt.io.read_textgrid(textgrid_file)

    # Get the target syllable interval
    syll_tier = tgt.get_tier_by_name(syll_tier_name)
    if syll_tier is not None and len(syll_tier.intervals) > 0:
        # Assuming only one target syllable interval
        target_interval = syll_tier.intervals[0]
        target_start = target_interval.start_time
        target_end = target_interval.end_time

        # Get the Tobi tier (point tier)
        tobi_tier = tg.get_tier_by_name(tobi_tier_name)
        if tobi_tier is not None:
            # Collect all points within the target syllable interval
            tobi_points = [
                {"mark": p.mark, "time": p.time}
                for p in tobi_tier.points
                if target_start <= p.time <= target_end
            ]
        else:
            tobi_points = []
    else:
        tobi_points = []

    if "sex" in config and speaker in config["sex"]:
        sex = config["sex"][speaker]
    else:
        sex = "NA"

    metadata = {
        "speaker": speaker,
        "item": item,
        "sex": sex,
        "nuclear_accent": tobi_points
    }
    metadata_list.append(metadata)
    return metadata_list

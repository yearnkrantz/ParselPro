import tgt, json
from pathlib import Path
import unicodedata

cfg = json.load(open("config.json", encoding="utf-8"))
tg_path = Path(r"C:\Users\Krantz\Island_Köln\YesNo\Niederländisch\final\VP001_WPANederlandsProd_Item03_PeterNegFakt_PosPeter_3.TextGrid")   # <-- change to a real TextGrid path
tg = tgt.io.read_textgrid(tg_path)
print("All tiers:", [t.name for t in tg.tiers])

tier_name = cfg["tiers"]["vowel_tier"]
# case-insensitive lookup
lower_to_tier = {t.name.strip().lower(): t for t in tg.tiers}
if tier_name.strip().lower() not in lower_to_tier:
    print("Requested tier not found. Available:", [t.name for t in tg.tiers])
else:
    t = lower_to_tier[tier_name.strip().lower()]
    def norm(s): return unicodedata.normalize("NFC", str(s or "").strip()).lower()
    if hasattr(t, "intervals"):
        for it in t.intervals[:40]:
            print(f"interval {it.start_time:.3f}-{it.end_time:.3f}: '{norm(it.text)}'")
    elif hasattr(t, "points"):
        for p in t.points[:40]:
            print(f"point {p.time:.3f}: '{norm(p.mark)}'")
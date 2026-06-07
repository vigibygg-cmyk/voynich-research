import os
import json
import glob
from collections import Counter

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_72_Spatial_Density_Heatmap.md"

def get_y_center(bounding_box):
    if not bounding_box: return -1
    y_min = bounding_box.get("y_min", -1)
    y_max = bounding_box.get("y_max", -1)
    if y_min != -1 and y_max != -1:
        return (y_min + y_max) / 2
    return -1

def get_zone(y):
    if y < 0: return "UNKNOWN"
    if y < 333: return "TOP (Flowers/Leaves)"
    if y < 666: return "MIDDLE (Stiebas)"
    return "BOTTOM (Roots/Bulbs)"

def build_heatmap():
    print("Pradedamas Spatial Density Heatmap skenavimas...")
    json_files = glob.glob(os.path.join(MAPPING_DIR, "*_mapping.json"))
    
    zone_prefixes = {
        "TOP (Flowers/Leaves)": Counter(),
        "MIDDLE (Stiebas)": Counter(),
        "BOTTOM (Roots/Bulbs)": Counter()
    }
    
    zone_suffixes = {
        "TOP (Flowers/Leaves)": Counter(),
        "MIDDLE (Stiebas)": Counter(),
        "BOTTOM (Roots/Bulbs)": Counter()
    }
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
        
        for block in data.get("text_blocks_mapping", []):
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "").replace("<->", "").replace("<>", "").replace("?", "")
                
                # Searching for bounding_box
                bbox = line.get("bounding_box")
                if not bbox:
                    # Could be bounding_box_local_A
                    for k in line.keys():
                        if "bounding_box" in k:
                            bbox = line[k]
                            break
                
                y = get_y_center(bbox)
                zone = get_zone(y)
                
                if zone == "UNKNOWN": continue
                
                words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
                
                for w in words:
                    if len(w) >= 3:
                        pref = w[:3]
                        suf = w[-2:]
                        zone_prefixes[zone][pref] += 1
                        zone_suffixes[zone][suf] += 1

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 72: Spatial Density Heatmap\n\n")
        f.write("This algorithm uses user created JSON coordinates (`y_min`, `y_max`), to divide manuscript pages into three zones: Top (Flowers), Middle (Stem) and Bottom (Roots). Then it is counted what prefixes (Commands) and suffixes (Doses/States) statistically cluster in each zone. This allows understanding if processing rules change depending on what plant part is nearby.\n\n")
        
        for zone in ["TOP (Flowers/Leaves)", "MIDDLE (Stem)", "BOTTOM (Roots/Bulbs)"]:
            f.write(f"## ZONA: {zone}\n")
            
            f.write("**Dominant Commands (Prefixes):**\n")
            for pref, count in zone_prefixes[zone].most_common(5):
                f.write(f"* `{pref}-`: {count} times\n")
                
            f.write("\n**Dominant States/Doses (Suffixes):**\n")
            for suf, count in zone_suffixes[zone].most_common(5):
                f.write(f"* `-{suf}`: {count} times\n")
            f.write("\n")
            
        f.write("---\n**Conclusion:** If certain suffixes (e.g. `-aiin`) massively dominate only near Roots, and others near Flowers, this proves the vertical dependence of Voynich syntax on drawing anatomy.\n")

    print(f"Heatmap baigtas. Ataskaita: {OUTPUT_REPORT}")

if __name__ == "__main__":
    build_heatmap()

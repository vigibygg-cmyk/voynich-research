import os
import json

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_45_Star_Color_Analysis.md"

# User provided color sequences
COLORS = {
    "f104r": ["RED", "YELLOW", "RED", "RED", "YELLOW", "RED", "YELLOW", "RED", "YELLOW", "RED", "YELLOW", "RED", "YELLOW"],
    "f116r": ["YELLOW", "RED", "YELLOW", "RED", "YELLOW", "RED", "YELLOW", "RED", "YELLOW", "RED"]
}

# Strict command roots (from f1v, f75v and external analyses)
COMMAND_ROOTS = ["qok", "qo", "cho", "daiin", "shol", "yt", "chok", "she", "ok", "dar", "ol", "chee", "or", "dor", "ot", "qot", "dal", "dol", "chot", "dai"]

def analyze_star_colors():
    print("Starting star color analysis...")
    
    report_lines = [
        "# Phase 45: Correlation of Star Colors and Temperature Operations",
        "\nUser identified star colors (Red, Yellow, White) on pages f104r and f116r. Testing the hypothesis that color indicates a thermal/state operation (Red = Fire/Heating; Yellow = Gentle maturation/Mixing; White = Washing/Cold).\n"
    ]
    
    color_stats = {
        "RED": {"cho": 0, "qok": 0, "yt": 0, "she": 0, "qo": 0, "other": 0, "total": 0},
        "YELLOW": {"cho": 0, "qok": 0, "yt": 0, "she": 0, "qo": 0, "other": 0, "total": 0}
    }
    
    for folio, colors in COLORS.items():
        file_path = os.path.join(MAPPING_DIR, f"{folio}_mapping.json")
        if not os.path.exists(file_path):
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        text_blocks = data.get("text_blocks_mapping", [])
        
        # Finding all line starts
        line_starts = []
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "").replace("<->", "").replace("???", "")
                words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
                if words:
                    first_word = words[0]
                    # Ar tai komanda?
                    found_root = "other"
                    for root in COMMAND_ROOTS:
                        if first_word.startswith(root):
                            if root in ["cho", "qok", "yt", "she", "qo"]:
                                found_root = root
                            else:
                                found_root = "other"
                            break
                    line_starts.append(found_root)
        
        # Linking with colors (assuming each star corresponds to a paragraph/line)
        # f104r and f116r stars mostly mark separate lines
        report_lines.append(f"\n## Folio: `{folio}`")
        for i, color in enumerate(colors):
            if i < len(line_starts):
                command = line_starts[i]
                color_stats[color]["total"] += 1
                color_stats[color][command] += 1
                report_lines.append(f"* **Star {i+1} ({color}):** Command `{command}-`")

    report_lines.append("\n## Summary: Colors and Operations")
    for color, stats in color_stats.items():
        report_lines.append(f"\n### {color} Stars (Total: {stats['total']})")
        for cmd, count in stats.items():
            if cmd != "total" and count > 0:
                report_lines.append(f"* Command `{cmd}-`: {count} times ({round((count/stats['total'])*100, 1)}%)")
                
    report_lines.append("\n**Conclusion:** Though sample is small, we can observe tendency if 'cho' (Heat) appears more often after RED star.")

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print(f"Color analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_star_colors()

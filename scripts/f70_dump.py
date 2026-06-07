import os

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

with open(FILE_ZL, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

with open("f70_dump.txt", "w", encoding='utf-8') as out:
    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 3 and parts[1] in ["f70r1", "f70r2"]:
            out.write(f"{parts[1]} | {parts[2]} | {parts[-1]}\n")

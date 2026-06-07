import cv2
import numpy as np
import os
import csv
import sys

sys.stdout.reconfigure(encoding='utf-8')

IMAGE_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\images_botany"
RESULTS_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Protokolai ir raportai\Phase_102_OpenCV_Results.csv"

def count_leaves(image_path):
    img = cv2.imread(image_path)
    if img is None: 
        print(f"Failed to load image: {image_path}")
        return 0
    
    # Resize to speed up processing and normalize
    # height, width = img.shape[:2]
    # img = cv2.resize(img, (width//2, height//2))
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Voynich green/olive hues typically fall in this range
    lower_green = np.array([25, 40, 40])
    upper_green = np.array([85, 255, 255])
    
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    leaf_count = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 200:  # Adjust threshold based on image resolution
            leaf_count += 1
            
    return leaf_count

results = []
print("Starting OpenCV Leaf Scan...")
for filename in os.listdir(IMAGE_DIR):
    if filename.endswith((".jpg", ".png", ".jpeg")):
        filepath = os.path.join(IMAGE_DIR, filename)
        folio_id = filename.split('.')[0]
        leaves = count_leaves(filepath)
        results.append({"Folio": folio_id, "Leaf_Count": leaves})
        print(f"Page {folio_id}: Counted leaves = {leaves}")

with open(RESULTS_FILE, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["Folio", "Leaf_Count"])
    writer.writeheader()
    writer.writerows(results)

print(f"\nScan complete. Results saved: {RESULTS_FILE}")

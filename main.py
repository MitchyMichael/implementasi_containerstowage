from formula import build_ship_geometry, build_40ft_slots, load_containers_from_csv, summarize_plan
from pso_class import PSO_Stowage_Planner

import random
import numpy as np
import pandas as pd
import os

# MARK: Data Fisik Kapal
# ===============================================================================================================================================
# --- Data Fisik Kapal ---
BAY_MAP = {
    1: -53.612, 3: -47.478, 5: -39.932, 7: -33.798, 9: -26.196, 11: -20.062, 13: -13.828, 15: -7.688, 17: -0.036, 19: 6.098002,
    21: 12.332, 23: 18.466, 25: 26.124, 27: 32.258, 29: 38.492, 31: 44.626, 33: 52.588, 35: 58.722
}
TIER_MAP = {
    2: 4.751, 4: 7.355, 6: 9.959, 8: 12.563, 10: 13.167,
    82: 17.055, 84: 17.671, 86: 20.286, 88: 22.902, 90: 25.517, 92: 28.133
}
ROW_MAP = {
    0: 0, 1: 2.518, 2: -2.518, 3: 5.036, 4: -5.036, 5: 7.554, 6: -7.554,
    7: 10.072, 8: -10.072
}

BAYS = sorted(list(BAY_MAP.keys()))
TIERS = sorted(list(TIER_MAP.keys()))
MAX_ROWS = 9

# MARK: Data Final Tata Letak Kapal
# ==================================================================================================================================================================================================================================================================================================================================================
# --- Data Final Tata Letak Kapal (Struktur 20ft) ---
SHIP_LAYOUT = {
    1: {2: [0, 1, 2], 4: [0, 1, 2], 6: [0, 1, 2], 8: [0, 1, 2], 82: [0, 1, 2, 3, 4, 5, 6], 84: [0, 1, 2, 3, 4, 5, 6], 86: [0, 1, 2, 3, 4, 5, 6], 88: [0, 1, 2, 3, 4, 5, 6]},
    3: {2: [0, 1, 2, 3, 4], 4: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4], 8: [0, 1, 2, 3, 4], 82: [0, 1, 2, 3, 4, 5, 6], 84: [0, 1, 2, 3, 4, 5, 6], 86: [0, 1, 2, 3, 4, 5, 6], 88: [0, 1, 2, 3, 4, 5, 6]},
    5: {2: [1, 2, 3, 4], 4: [1, 2, 3, 4, 5, 6], 6: [1, 2, 3, 4, 5, 6], 8: [1, 2, 3, 4, 5, 6], 10: [1, 2, 3, 4, 5, 6], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    7: {2: [1, 2, 3, 4, 5, 6], 4: [1, 2, 3, 4, 5, 6], 6: [1, 2, 3, 4, 5, 6], 8: [1, 2, 3, 4, 5, 6], 10: [1, 2, 3, 4, 5, 6], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4]},
    9: {2: [1, 2, 3, 4, 5, 6], 4: [1, 2, 3, 4, 5, 6], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 7]},
    11: {2: [1, 2, 3, 4, 5, 6, 7], 4: [1, 2, 3, 4, 5, 6, 7], 6: [1, 2, 3, 4, 5, 6, 7], 8: [1, 2, 3, 4, 5, 6, 7], 10: [1, 2, 3, 4, 5, 6, 7], 82: [0, 1, 2, 3, 4, 5, 6, 7], 84: [0, 1, 2, 3, 4, 5, 6, 7], 86: [0, 1, 2, 3, 4, 5, 6, 7], 88: [0, 1, 2, 3, 4, 5, 7], 90: [0, 1, 2, 3, 4, 5, 7]},
    13: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    15: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    17: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    19: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    21: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    23: {2: [1, 2, 3, 4, 5, 6, 7, 8], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    25: {2: [1, 2, 3, 4, 5, 6, 7], 4: [1, 2, 3, 4, 5, 6, 7], 6: [1, 2, 3, 4, 5, 6, 7], 8: [1, 2, 3, 4, 5, 6, 7], 10: [1, 2, 3, 4, 5, 6, 7], 82: [0, 1, 2, 3, 4, 5, 6, 7], 84: [0, 1, 2, 3, 4, 5, 6, 7], 86: [0, 1, 2, 3, 4, 5, 6, 7], 88: [0, 1, 2, 3, 4, 5, 6, 7], 90: [1, 3, 5, 7]},
    27: {2: [1, 2, 3, 4, 5, 6], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    29: {2: [1, 2, 3, 4, 5, 6], 4: [1, 2, 3, 4, 5, 6, 7, 8], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    31: {2: [1, 2, 3, 4], 4: [1, 2, 3, 4, 5, 6], 6: [1, 2, 3, 4, 5, 6, 7, 8], 8: [1, 2, 3, 4, 5, 6, 7, 8], 10: [1, 2, 3, 4, 5, 6, 7, 8], 82: [0, 1, 2, 3, 4, 5, 6, 7, 8], 84: [0, 1, 2, 3, 4, 5, 6, 7, 8], 86: [0, 1, 2, 3, 4, 5, 6, 7, 8], 88: [0, 1, 2, 3, 4, 5, 6, 7, 8], 90: [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    33: {82: [1, 2, 3, 4, 5, 6, 7, 8], 84: [1, 2, 3, 4, 5, 6, 7, 8], 86: [1, 2, 3, 4, 5, 6, 7, 8], 88: [1, 2, 3, 4, 5, 6, 7, 8], 90: [1, 2, 3, 4, 5, 6, 7, 8], 92: [1, 2, 3, 4, 5, 6, 7, 8]},
    35: {82: [1, 2, 3, 4, 5, 6, 7, 8], 84: [1, 2, 3, 4, 5, 6, 7, 8], 86: [1, 2, 3, 4, 5, 6, 7, 8], 88: [1, 2, 3, 4, 5, 6, 7, 8], 90: [1, 2, 3, 4, 5, 6, 7, 8], 92: [1, 2, 3, 4, 5, 6, 7, 8]}
}

# MARK: Aturan Khusus Kontainer 40ft
# ==============================================================================================================================================================================
# --- ATURAN KHUSUS UNTUK KONTAINER 40 KAKI ---
# 1. Daftar bay genap yang diizinkan untuk 40ft
ALLOWED_40FT_BAYS = {2, 6, 10, 14, 18, 22, 26, 30, 34}

# 2. Daftar Pengecualian (blacklist) untuk slot 40ft yang tidak valid
INVALID_40FT_SLOTS = {
    # Format: (Bay Genap, Row, Tier)
    (6, 5, 2), (6, 6, 2), (6, 0, 90), (6, 1, 90), (6, 2, 90), (6, 3, 90), (6, 4, 90),
    (10, 7, 2), (10, 7, 4), (10, 8, 6), (10, 8, 8), (10, 8, 10), (10, 6, 88), (10, 8, 82), (10, 8, 84), (10, 8, 86), (10, 8, 88),
    (26, 7, 2), 
    (26, 8, 4), (26, 8, 6), (26, 8, 8), (26, 8, 10), (26, 8, 82), (26, 8, 84), (26, 8, 86), (26, 8, 88), (26, 8, 90),
    (30, 5, 2), (30, 6, 2), (30, 7, 4), (30, 8, 4),
}

# --- KONFIGURASI DAN EKSEKUSI ---
VALID_SLOT_MASK_20FT, SLOT_PROPERTIES_20FT = build_ship_geometry(TIERS, BAYS, MAX_ROWS, SHIP_LAYOUT, ROW_MAP, BAY_MAP, TIER_MAP)
VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT = build_40ft_slots(VALID_SLOT_MASK_20FT, SLOT_PROPERTIES_20FT, BAYS, ALLOWED_40FT_BAYS, TIERS, INVALID_40FT_SLOTS)
TOTAL_VALID_SLOTS_20FT, TOTAL_VALID_SLOTS_40FT = len(SLOT_PROPERTIES_20FT), len(VALID_PLACEMENTS_40FT)

# --- KONFIGURASI ALGORITMA ---
NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD = 400, 200
NUM_PARTICLES, MAX_ITERATIONS = 50, 200
WEIGHT_PENALTY = {"vertical_moment": 0.0001, "longitudinal_balance": 100.0, "stability_tcg": 8000.0}

print("✅ Cell 2: Konfigurasi Geometri dan Aturan siap digunakan.")
print(f"   - Slot 20ft Valid: {TOTAL_VALID_SLOTS_20FT}")
print(f"   - Slot 40ft Valid (setelah filter): {TOTAL_VALID_SLOTS_40FT}")

# MARK: Final
# ================================================================================================================================================================
# Folder export
EXPORT_DIR = "export"
os.makedirs(EXPORT_DIR, exist_ok=True)

# Ganti nama file ini dengan nama file data kontainer Anda
csv_filename = os.path.join(EXPORT_DIR, "containers.csv")

# Membuat file CSV dummy jika tidak ada, untuk keperluan pengujian
if not os.path.exists(csv_filename):
    print(f"File '{csv_filename}' tidak ditemukan. Membuat file dummy...")
    num_total_containers = TOTAL_VALID_SLOTS_20FT 
    ids = [f'CONT{i:04d}' for i in range(1, num_total_containers + 1)]
    weights = [random.uniform(5, 28) for _ in range(num_total_containers)]
    sizes = [40 if random.random() < 0.35 else 20 for _ in range(num_total_containers)]
    pd.DataFrame({'Container_ID': ids, 'Weight_ton': weights, 'Size': sizes}).to_csv(csv_filename, index=False)

all_containers = load_containers_from_csv(csv_filename)

if all_containers:
    num_avail_20ft, num_avail_40ft = sum(1 for c in all_containers if c['size'] == 20), sum(1 for c in all_containers if c['size'] == 40)
    if num_avail_20ft < NUM_20FT_TO_LOAD or num_avail_40ft < NUM_40FT_TO_LOAD:
        print(f"❌ Error: Jumlah kontainer di CSV tidak mencukupi.")
        print(f"   - Butuh 20ft: {NUM_20FT_TO_LOAD}, Tersedia: {num_avail_20ft}")
        print(f"   - Butuh 40ft: {NUM_40FT_TO_LOAD}, Tersedia: {num_avail_40ft}")
    else:
        # Data kondisi kapal
        lightship_properties = {'weight': 5560400, 'lcg': 7.83, 'vcg': 4, 'tcg': 0}
        tanks_data = [
            {'name': 'FO Tank 1 Port', 'weight': 31618,  'lcg': -0.936, 'vcg': 12.647, 'tcg': -6.460},
            {'name': 'FO Tank 1 Stbd', 'weight': 31618,  'lcg': -0.936, 'vcg': 12.647, 'tcg': 6.460},
            {'name': 'AFT PEAK WB', 'weight': 131200, 'lcg': -72.192, 'vcg': 8.592, 'tcg': 0.00},
            {'name': 'WB TK NO.1', 'weight': 547835, 'lcg': -68.995, 'vcg': 6.107, 'tcg': 0.0},
            {'name': 'WB TK (P) NO.2', 'weight': 343807, 'lcg': -19.49, 'vcg': 2.455, 'tcg': -2.620},
            {'name': 'WB TK (S) NO.2', 'weight': 240665, 'lcg': -19.49, 'vcg': 2.455, 'tcg': 2.620},
            {'name': 'WB TK (P) NO.3', 'weight': 140146, 'lcg': -30.6236, 'vcg': 0.825, 'tcg': -3.493},
            {'name': 'WB TK (S) NO.3', 'weight': 91095, 'lcg': -30.6236, 'vcg': 0.825, 'tcg': 3.493},
            {'name': 'WB TK (P) NO.4', 'weight': 390410, 'lcg': 39.7517,  'vcg': 0.782, 'tcg': -4.922},
            {'name': 'WB TK (S) NO.4', 'weight': 253766, 'lcg': 39.7517,  'vcg': 0.782, 'tcg': 4.922},
            {'name': 'WB TK (P) NO.5', 'weight': 428948, 'lcg': 46.3378,  'vcg': 0.766, 'tcg': -5.347},
            {'name': 'WB TK (S) NO.5', 'weight': 403211, 'lcg': 46.3378,  'vcg': 0.766, 'tcg': 5.347},
            {'name': 'WB TK (P) NO.6', 'weight': 290775, 'lcg': 54.6918,  'vcg': 0.821, 'tcg': -4.099},
            {'name': 'WB TK (S) NO.6', 'weight': 290775, 'lcg': 54.6918,  'vcg': 0.821, 'tcg': 4.099},
            {'name': 'Sludge Tank', 'weight': 33430, 'lcg': -57.9533, 'vcg': 1.303, 'tcg': 0},
            {'name': 'Bilge Holding Tank', 'weight': 10165, 'lcg': -58.9698, 'vcg': 1.105, 'tcg': -3.131}
        ]
        
        # --- PERUBAHAN DI SINI ---
        
        # Baris ini dinonaktifkan
        # target_lcg_value = calculate_target_lcg(lightship_properties, tanks_data)

        # Kode BARU untuk meminta input LCG dari user
        target_lcg_value = None
        while target_lcg_value is None:
            try:
                lcg_input = input("➡️ Masukkan Target LCG yang diinginkan (contoh: 7.5): ")
                target_lcg_value = float(lcg_input)
                print(f"✅ Target LCG diatur ke: {target_lcg_value} m")
            except ValueError:
                print("❌ Input tidak valid. Harap masukkan angka.")
        
        # --- Akhir Perubahan ---

        # Buat instance planner dan jalankan optimasi
        stowage_planner = PSO_Stowage_Planner(
            NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, all_containers=all_containers, lightship_data=lightship_properties, tanks_data=tanks_data,
            slot_properties_20ft=SLOT_PROPERTIES_20FT, valid_mask_20ft=VALID_SLOT_MASK_20FT,
            valid_placements_40ft=VALID_PLACEMENTS_40FT, slot_properties_40ft=SLOT_PROPERTIES_40FT,
            target_lcg=target_lcg_value
        )
        best_plan, best_summary = stowage_planner.run(MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY)
        
        # Tampilkan hasil ringkasan dan denah
        summarize_plan(best_summary, target_lcg_value)
        if best_plan is not None:
            print("\n\n--- 🗂️ Denah Muatan Lengkap (Tampilan per Tier dari Atas ke Bawah) ---")
            CELL_WIDTH = 12
            for tier_id in sorted(TIERS, reverse=True):
                t_idx = TIERS.index(tier_id)
                tier_plan = best_plan[t_idx, :, :]
                if np.any(tier_plan != 0):
                    print(f"\n\n--- Denah untuk Tier {tier_id:02d} ---")
                    header = "Row".ljust(CELL_WIDTH)
                    b_idx = 0
                    while b_idx < len(BAYS):
                        bay_id = BAYS[b_idx]
                        if b_idx + 1 < len(BAYS) and BAYS[b_idx+1] == bay_id + 2:
                            header += f"Bay{bay_id+1:02d} (40ft)".center(CELL_WIDTH * 2)
                            b_idx += 2
                        else: header += f"Bay{bay_id:02d}".ljust(CELL_WIDTH); b_idx += 1
                    print(header); print("-" * len(header))
                    for r_idx in range(MAX_ROWS):
                        row_str, has_content = "", False
                        b_idx_print = 0
                        while b_idx_print < len(BAYS):
                            coords = (t_idx, b_idx_print, r_idx)
                            if VALID_SLOT_MASK_20FT[coords]:
                                content_val = tier_plan[b_idx_print, r_idx]
                                if content_val != 0 and content_val != 'OCCUPIED_40FT':
                                    container = stowage_planner.container_dict[content_val]
                                    if container['size'] == 40:
                                        has_content = True
                                        row_str += f"{str(content_val)}".center(CELL_WIDTH * 2)
                                        b_idx_print += 2; continue
                                    else: has_content = True; row_str += str(content_val).ljust(CELL_WIDTH)
                                else: row_str += ".".ljust(CELL_WIDTH)
                            else: row_str += "".ljust(CELL_WIDTH)
                            b_idx_print += 1
                        if has_content: print(f"Row {r_idx:02d}".ljust(CELL_WIDTH) + row_str)
            stowage_planner.export_plan_to_excel(best_plan, TIERS, BAYS, "Hasil_Stowage_Plan_Final.xlsx")
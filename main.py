from formula import load_containers_from_csv, summarize_plan
from pso_class import PSO_Stowage_Planner
from ship_data import ship_data

import random
import numpy as np
import pandas as pd
import os

TOTAL_VALID_SLOTS_20FT, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, SLOT_PROPERTIES_20FT, VALID_SLOT_MASK_20FT, VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY, BAYS, MAX_ROWS = ship_data()

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
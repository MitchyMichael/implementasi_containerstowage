import numpy as np
import os
import pandas as pd
import random

from format_containerexcel import make_csv_from_excel

# MARK: Build ship geo
def build_ship_geometry(TIERS, BAYS, MAX_ROWS, SHIP_LAYOUT, ROW_MAP, BAY_MAP, TIER_MAP):
    """Membangun geometri kapal dari SHIP_LAYOUT."""
    num_tiers, num_bays = len(TIERS), len(BAYS)
    valid_mask = np.full((num_tiers, num_bays, MAX_ROWS), False, dtype=bool)
    slot_properties = {}
    tier_indices = {tier_id: i for i, tier_id in enumerate(TIERS)}
    bay_indices = {bay_id: i for i, bay_id in enumerate(BAYS)}
    for bay_id, tiers_data in SHIP_LAYOUT.items():
        if bay_id not in bay_indices: continue
        b_idx = bay_indices[bay_id]
        for tier_id, valid_rows in tiers_data.items():
            if tier_id not in tier_indices: continue
            t_idx = tier_indices[tier_id]
            for r_idx in valid_rows:
                if r_idx in ROW_MAP:
                    valid_mask[t_idx, b_idx, r_idx] = True
                    lcg, vcg, tcg = BAY_MAP[bay_id], TIER_MAP[tier_id], ROW_MAP[r_idx]
                    if tier_id == 82 and bay_id in [33, 35]: vcg = 15.055
                    slot_properties[(t_idx, b_idx, r_idx)] = {'lcg': lcg, 'vcg': vcg, 'tcg': tcg}
    return valid_mask, slot_properties

# MARK: Build 40ft
def build_40ft_slots(valid_mask, slot_properties_20ft, BAYS, ALLOWED_40FT_BAYS, TIERS, INVALID_40FT_SLOTS):
    """Mencari semua kemungkinan penempatan untuk kontainer 40ft dengan memeriksa daftar pengecualian."""
    valid_placements_40ft, properties_40ft = [], {}
    for b_idx in range(len(BAYS) - 1):
        bay1_id, bay2_id = BAYS[b_idx], BAYS[b_idx + 1]
        if bay1_id % 2 != 1 or bay2_id != bay1_id + 2: continue
        even_bay_representation = bay1_id + 1
        if even_bay_representation not in ALLOWED_40FT_BAYS: continue
        for t_idx in range(valid_mask.shape[0]):
            tier_id = TIERS[t_idx]
            for r_idx in range(valid_mask.shape[2]):
                if (even_bay_representation, r_idx, tier_id) in INVALID_40FT_SLOTS: continue
                if valid_mask[t_idx, b_idx, r_idx] and valid_mask[t_idx, b_idx + 1, r_idx]:
                    coords_40ft = (t_idx, b_idx, r_idx)
                    valid_placements_40ft.append(coords_40ft)
                    props1 = slot_properties_20ft[(t_idx, b_idx, r_idx)]
                    props2 = slot_properties_20ft[(t_idx, b_idx + 1, r_idx)]
                    properties_40ft[coords_40ft] = {'lcg': (props1['lcg'] + props2['lcg']) / 2.0, 'vcg': props1['vcg'], 'tcg': props1['tcg']}
    return valid_placements_40ft, properties_40ft

# MARK: Calculate target lcg
def calculate_target_lcg(lightship_data, tanks_data):
    """Menghitung LCG target berdasarkan kondisi kapal tanpa kargo."""
    total_weight, total_moment_l = lightship_data['weight'], lightship_data['weight'] * lightship_data['lcg']
    for tank in tanks_data:
        total_weight += tank['weight']; total_moment_l += tank['weight'] * tank['lcg']
    if total_weight == 0: return 0
    return total_moment_l / total_weight

# MARK: Validitas (Debug)
# --- Fungsi Pengecekan Validitas (Untuk Debugging) ---
def cek_validitas_slot_40ft(bay_genap, row, tier, ALLOWED_40FT_BAYS, INVALID_40FT_SLOTS, SHIP_LAYOUT):
    """Fungsi mandiri untuk mengecek apakah sebuah slot 40ft valid berdasarkan semua aturan."""
    if bay_genap not in ALLOWED_40FT_BAYS: return False, f"Ditolak: Bay {bay_genap} tidak diizinkan."
    if (bay_genap, row, tier) in INVALID_40FT_SLOTS: return False, f"Ditolak: Slot ada di daftar pengecualian."
    try:
        bay_ganjil1, bay_ganjil2 = bay_genap - 1, bay_genap + 1
        if row not in SHIP_LAYOUT[bay_ganjil1][tier] or row not in SHIP_LAYOUT[bay_ganjil2][tier]:
            return False, f"Ditolak: Komponen 20ft tidak lengkap."
    except KeyError: return False, f"Ditolak: Komponen Bay/Tier tidak ditemukan."
    return True, "✅ Slot Valid."

# MARK: Load container
def load_containers_from_csv(filename):
    """Membaca data kontainer dari file CSV, termasuk ukurannya."""
    if not os.path.exists(filename):
        print(f"❌ Error: File tidak ditemukan di '{os.path.abspath(filename)}'.")
        return None
    try:
        df = pd.read_csv(filename)
        df = df.rename(columns={'Container_ID': 'id', 'Weight_ton': 'weight', 'Size': 'size'})
        df['weight'] = df['weight'] * 1000
        if 'id' not in df.columns or 'weight' not in df.columns or 'size' not in df.columns:
            raise KeyError("Kolom yang dibutuhkan ('id', 'weight', 'size') tidak ditemukan.")
        # print(f"✅ Berhasil memuat {len(df)} kontainer dari file {filename}.")
        return df.to_dict('records')
    except Exception as e:
        print(f"❌ Terjadi error saat membaca file: {e}")
        return None
    
# MARK: Summarize Plan
def summarize_plan(summary, target_lcg):
    """Memberikan ringkasan kualitas dari hasil akhir denah muatan."""
    print("\n--- 📊 Ringkasan Hasil Stowage Plan Terbaik ---")
    if not summary:
        print("Tidak ada solusi yang ditemukan.")
        return

    print(f"Total Fitness: {summary['fitness']:.4f}")
    print(f"Total Berat Kapal (Displacement): {summary['total_weight']/1000:.2f} Ton")
    print("--- Stabilitas Kapal ---")

    final_lcg, final_vcg, final_tcg = summary['ship_lcg'], summary['ship_vcg'], summary['ship_tcg']
    lcg_diff = abs(final_lcg - target_lcg)
    lcg_status = "✅ Berhasil" if lcg_diff < 1.0 else "⚠️ Perlu Penyesuaian"
    print(f"   - LCG Total: {final_lcg:.4f} m (Target: {target_lcg:.4f} m) - Status: {lcg_status}")
    print(f"   - VCG Total: {final_vcg:.4f} m")
    tcg_status = "✅ Berhasil" if abs(final_tcg) < 0.2 else "⚠️ Gagal"
    print(f"   - TCG Total: {final_tcg:.4f} m (Target: |TCG| < 0.2 m) - Status: {tcg_status}")

# MARK: Get Containers
def get_containers(TOTAL_VALID_SLOTS_20FT):
    EXPORT_DIR = "export"
    os.makedirs(EXPORT_DIR, exist_ok=True)

    # Ganti nama file ini dengan nama file data kontainer Anda
    csv_filename = os.path.join(EXPORT_DIR, "containers.csv")
    xlsx_filename = os.path.join("./archive", "container.xlsx")
    if os.path.exists(xlsx_filename):
        print("Ada file excel")
        make_csv_from_excel("./archive/container.xlsx", "./export/containers_mapped.csv")
        csv_filename = os.path.join(EXPORT_DIR, "containers_mapped.csv")
        all_containers = load_containers_from_csv(csv_filename) 
        return all_containers
    
    else:
        # Membuat file CSV dummy jika tidak ada, untuk keperluan pengujian
        if not os.path.exists(csv_filename):
            print(f"File '{csv_filename}' tidak ditemukan. Membuat file dummy...")
            num_total_containers = TOTAL_VALID_SLOTS_20FT 
            ids = [f'CONT{i:04d}' for i in range(1, num_total_containers + 1)]
            weights = [random.uniform(5, 28) for _ in range(num_total_containers)]
            sizes = [40 if random.random() < 0.35 else 20 for _ in range(num_total_containers)]
            pd.DataFrame({'Container_ID': ids, 'Weight_ton': weights, 'Size': sizes}).to_csv(csv_filename, index=False)

        all_containers = load_containers_from_csv(csv_filename) 
        return all_containers

# MARK: Formula Target LCG Value
def calculate_lcg():
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
    return target_lcg_value

# MARK: Formula Best Plan
def print_bestplan(best_plan, stowage_planner, BAYS, TIERS, MAX_ROWS, VALID_SLOT_MASK_20FT):
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
            
            print("MAX_ROWS", MAX_ROWS)
            evens = list(range(MAX_ROWS - 1, -1, -1))  # 8..0
            evens = [n for n in evens if n % 2 == 0]
            odds = [n for n in range(MAX_ROWS) if n % 2 == 1]
            order = evens + odds

            # Kalau row ganjil
            if MAX_ROWS%2 != 0:
                for i, r_idx in enumerate(range(MAX_ROWS)):
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
                    if has_content: print(f"Row {order[i]:02d}".ljust(CELL_WIDTH) + row_str)
            
            # Kalau row genap
            else:
                for i, r_idx in enumerate(range(MAX_ROWS)):
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
                    if has_content: print(f"Row {(int(order[i]+1)):02d}".ljust(CELL_WIDTH) + row_str)
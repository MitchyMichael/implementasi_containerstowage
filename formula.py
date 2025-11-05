import numpy as np
import os
import pandas as pd

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
        print(f"✅ Berhasil memuat {len(df)} kontainer dari file {filename}.")
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

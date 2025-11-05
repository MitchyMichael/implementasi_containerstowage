from collections import defaultdict
from formula import build_ship_geometry, build_40ft_slots, load_containers_from_csv, summarize_plan

import random
import numpy as np
import copy
import pandas as pd
import os

# MARK: Data Fisik Kapal
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

# MARK: Kelas Utama PSO
# Cell 4: Kelas Utama PSO (Particle Swarm Optimization) - DENGAN ATURAN ON DECK FLEKSIBEL
class PSO_Stowage_Planner:
    """Kelas utama untuk menjalankan algoritma PSO untuk Stowage Planning."""
    def __init__(self, all_containers, lightship_data, tanks_data, 
                 slot_properties_20ft, valid_mask_20ft, 
                 valid_placements_40ft, slot_properties_40ft, target_lcg):
        self.lightship_weight, self.lightship_lcg, self.lightship_vcg, self.lightship_tcg = lightship_data.values()
        self.tanks_data, self.slot_properties_20ft, self.valid_mask = tanks_data, slot_properties_20ft, valid_mask_20ft
        self.valid_slots_coords_20ft, self.valid_placements_40ft = list(slot_properties_20ft.keys()), valid_placements_40ft
        self.slot_properties_40ft, self.position_shape, self.target_lcg = slot_properties_40ft, valid_mask_20ft.shape, target_lcg
        self.gbest_fitness, self.gbest_position, self.gbest_summary, self.swarm = float('inf'), None, {}, []

        print("🔍 Memisahkan kontainer berdasarkan ukuran...")
        containers_20ft = sorted([c for c in all_containers if c['size'] == 20], key=lambda x: x['weight'], reverse=True)
        containers_40ft = sorted([c for c in all_containers if c['size'] == 40], key=lambda x: x['weight'], reverse=True)
        self.containers_to_load_20ft, self.containers_to_load_40ft = containers_20ft[:NUM_20FT_TO_LOAD], containers_40ft[:NUM_40FT_TO_LOAD]
        self.container_dict = {c['id']: c for c in self.containers_to_load_20ft + self.containers_to_load_40ft}
        print(f"   - {len(self.containers_to_load_20ft)} kontainer 20ft dan {len(self.containers_to_load_40ft)} kontainer 40ft akan dimuat.")

    def _create_base_plan(self):
        """Membangun denah dasar yang dari awal sudah mematuhi semua aturan constraint, termasuk aturan On Deck."""
        print("🏗️  Membuat denah dasar yang valid (dengan aturan On Deck)...")
        base_position = np.zeros(self.position_shape, dtype=object)

        # 1. Tempatkan semua kontainer 40ft
        slots_40ft_sorted = sorted(self.valid_placements_40ft, key=lambda c: self.slot_properties_40ft[c]['vcg'])
        for i in range(min(len(self.containers_to_load_40ft), len(slots_40ft_sorted))):
            container, coords = self.containers_to_load_40ft[i], slots_40ft_sorted[i]
            t_idx, b_idx, r_idx = coords
            base_position[t_idx, b_idx, r_idx], base_position[t_idx, b_idx + 1, r_idx] = container['id'], 'OCCUPIED_40FT'

        # 2. Setelah 40ft ditempatkan, tentukan semua "plafon" di Under Deck
        ceilings = {}
        for b_idx in range(self.position_shape[1]):
            for r_idx in range(self.position_shape[2]):
                max_tier = -1
                for t_idx in range(self.position_shape[0]):
                    if base_position[t_idx, b_idx, r_idx] != 0:
                        max_tier = max(max_tier, t_idx)
                if max_tier != -1:
                    ceilings[(b_idx, r_idx)] = max_tier
        
        # 3. Cari semua slot 20ft yang aman dengan aturan On Deck/Under Deck
        safe_20ft_slots = []
        for coords in self.valid_slots_coords_20ft:
            t_idx, b_idx, r_idx = coords
            tier_id = TIERS[t_idx]
            
            # Lewati jika slot sudah terisi
            if base_position[coords] != 0:
                continue

            is_safe = False
            # Cek apakah slot berada di Under Deck atau On Deck
            if tier_id < 82: # UNDER DECK
                ceiling = ceilings.get((b_idx, r_idx), -1)
                if ceiling == -1 or t_idx < ceiling:
                    is_safe = True
            else: # ON DECK
                is_safe = True # Aturan plafon tidak berlaku di On Deck
            
            if is_safe:
                safe_20ft_slots.append(coords)
        
        safe_20ft_slots.sort(key=lambda c: self.slot_properties_20ft[c]['vcg'])

        # 4. Isi slot-slot aman tersebut dengan kontainer 20ft
        for i, cid_data in enumerate(self.containers_to_load_20ft):
            if i < len(safe_20ft_slots):
                base_position[safe_20ft_slots[i]] = cid_data['id']
            else:
                break
        
        return self._repair_plan(base_position)


    def _initialize_swarm(self, base_plan):
        print("🚀 Menginisialisasi partikel...")
        for _ in range(NUM_PARTICLES):
            position = copy.deepcopy(base_plan)
            for _ in range(25):
                position = self._safe_swap(position)
            position = self._repair_plan(position)
            fitness, summary = self._calculate_fitness(position)
            particle = {'position': position, 'pbest_position': copy.deepcopy(position), 'pbest_fitness': fitness}
            self.swarm.append(particle)
            if fitness < self.gbest_fitness:
                self.gbest_fitness, self.gbest_position, self.gbest_summary = fitness, copy.deepcopy(position), summary
        print("Inisialisasi selesai.")

    # --- FUNGSI PERBAIKAN DENGAN ATURAN ON DECK BARU ---
    def _repair_plan(self, plan):
        repaired_plan = np.zeros(self.position_shape, dtype=object)
        
        # 1. Kunci semua posisi 40ft
        containers_40ft = []
        for coords, cid in np.ndenumerate(plan):
            if cid != 0 and cid != 'OCCUPIED_40FT' and self.container_dict.get(cid) and self.container_dict[cid]['size'] == 40:
                repaired_plan[coords] = cid
                repaired_plan[coords[0], coords[1]+1, coords[2]] = 'OCCUPIED_40FT'
                containers_40ft.append(cid)
        
        # 2. Tentukan semua "plafon"
        ceilings = {}
        for b_idx in range(self.position_shape[1]):
            for r_idx in range(self.position_shape[2]):
                max_tier = -1
                for t_idx in range(self.position_shape[0]):
                    if repaired_plan[t_idx, b_idx, r_idx] != 0:
                        max_tier = max(max_tier, t_idx)
                if max_tier != -1:
                    ceilings[(b_idx, r_idx)] = max_tier
        
        # 3. Kumpulkan & urutkan SEMUA kontainer 20ft
        all_20ft_containers = [cid for cid in np.ravel(plan) if cid != 0 and cid != 'OCCUPIED_40FT' and self.container_dict.get(cid) and self.container_dict[cid]['size'] == 20]
        sorted_20ft_ids = sorted(all_20ft_containers, key=lambda cid: self.container_dict[cid]['weight'], reverse=True)

        # 4. Cari SEMUA slot yang aman untuk 20ft dengan aturan On Deck/Under Deck
        safe_20ft_slots = []
        for coords in self.valid_slots_coords_20ft:
            t_idx, b_idx, r_idx = coords
            tier_id = TIERS[t_idx]

            if repaired_plan[coords] != 0: continue

            is_safe = False
            if tier_id < 82: # UNDER DECK
                ceiling = ceilings.get((b_idx, r_idx), -1)
                if ceiling == -1 or t_idx < ceiling:
                    is_safe = True
            else: # ON DECK
                is_safe = True
            
            if is_safe:
                safe_20ft_slots.append(coords)
        
        safe_20ft_slots.sort(key=lambda c: self.slot_properties_20ft[c]['vcg'])

        # 5. Isi kembali slot aman dengan kontainer 20ft terurut
        for i, cid in enumerate(sorted_20ft_ids):
            if i < len(safe_20ft_slots):
                repaired_plan[safe_20ft_slots[i]] = cid

        return repaired_plan

    def _safe_swap(self, position):
        new_pos = position
        if random.random() < 0.5:
            ids_20ft = [(c, v) for c, v in np.ndenumerate(new_pos) if v != 0 and v != 'OCCUPIED_40FT' and self.container_dict.get(v, {}).get('size') == 20]
            if len(ids_20ft) >= 2: (c1, v1), (c2, v2) = random.sample(ids_20ft, 2); new_pos[c1], new_pos[c2] = v2, v1
        else:
            ids_40ft = [(c, v) for c, v in np.ndenumerate(new_pos) if v != 0 and v != 'OCCUPIED_40FT' and self.container_dict.get(v, {}).get('size') == 40]
            if len(ids_40ft) >= 2:
                (c1, v1), (c2, v2) = random.sample(ids_40ft, 2)
                new_pos[c1], new_pos[c2] = v2, v1
                c1_occupied, c2_occupied = (c1[0], c1[1]+1, c1[2]), (c2[0], c2[1]+1, c2[2])
                new_pos[c1_occupied], new_pos[c2_occupied] = new_pos[c2_occupied], new_pos[c1_occupied]
        return new_pos

    def _update_particle_position(self, particle):
        new_pos = copy.deepcopy(particle['pbest_position'])
        for _ in range(5):
            new_pos = self._safe_swap(new_pos)
        return new_pos

    def _calculate_fitness(self, plan):
        cargo_weight, cargo_moment_l, cargo_moment_v, cargo_moment_t = 0, 0, 0, 0
        for coords, c_id in np.ndenumerate(plan):
            if c_id != 0 and c_id != 'OCCUPIED_40FT' and c_id in self.container_dict:
                container, weight = self.container_dict[c_id], self.container_dict[c_id]['weight']
                props = self.slot_properties_20ft.get(coords) if container['size'] == 20 else self.slot_properties_40ft.get(coords)
                if props:
                    cargo_weight += weight; cargo_moment_l += weight * props['lcg']
                    cargo_moment_v += weight * props['vcg']; cargo_moment_t += weight * props['tcg']
        lightship_moment_l, lightship_moment_v, lightship_moment_t = self.lightship_weight*self.lightship_lcg, self.lightship_weight*self.lightship_vcg, self.lightship_weight*self.lightship_tcg
        tanks_weight, tanks_moment_l, tanks_moment_v, tanks_moment_t = 0, 0, 0, 0
        for tank in self.tanks_data:
            tanks_weight += tank['weight']; tanks_moment_l += tank['weight']*tank['lcg']
            tanks_moment_v += tank['weight']*tank['vcg']; tanks_moment_t += tank['weight']*tank['tcg']
        total_weight = self.lightship_weight + cargo_weight + tanks_weight
        if total_weight == 0: return float('inf'), {}
        total_moment_l, total_moment_v, total_moment_t = lightship_moment_l+cargo_moment_l+tanks_moment_l, lightship_moment_v+cargo_moment_v+tanks_moment_v, lightship_moment_t+cargo_moment_t+tanks_moment_t
        final_ship_lcg, final_ship_vcg, final_ship_tcg = total_moment_l/total_weight, total_moment_v/total_weight, total_moment_t/total_weight
        penalties = defaultdict(float)
        penalties["vertical_moment"], penalties["longitudinal_balance"] = total_moment_v, abs(final_ship_lcg - self.target_lcg)
        if abs(final_ship_tcg) > 0.2: penalties["stability_tcg"] = abs(final_ship_tcg) - 0.2
        total_fitness = sum(WEIGHT_PENALTY[key] * val for key, val in penalties.items())
        summary = {"fitness": total_fitness, "ship_lcg": final_ship_lcg, "ship_vcg": final_ship_vcg, "ship_tcg": final_ship_tcg, "total_weight": total_weight}
        return total_fitness, summary

    def run(self):
        base_plan = self._create_base_plan()
        self._initialize_swarm(base_plan)
        print("\n--- Memulai Iterasi PSO ---")
        for i in range(MAX_ITERATIONS):
            for particle in self.swarm:
                repaired_position = self._repair_plan(self._update_particle_position(particle))
                new_fitness, new_summary = self._calculate_fitness(repaired_position)
                if new_fitness < particle['pbest_fitness']: particle['pbest_fitness'], particle['pbest_position'] = new_fitness, copy.deepcopy(repaired_position)
                if new_fitness < self.gbest_fitness: self.gbest_fitness, self.gbest_position, self.gbest_summary = new_fitness, copy.deepcopy(repaired_position), new_summary
            if (i + 1) % 10 == 0: print(f"Iterasi {i+1}/{MAX_ITERATIONS} | Best Fitness: {self.gbest_fitness:.2f}")
        print("\n--- Optimasi Selesai ---")
        return self.gbest_position, self.gbest_summary

    def export_plan_to_excel(self, plan, filename="stowage_plan.xlsx"):
        try:
            from pathlib import Path

            # Pastikan folder export ada, dan pakai nama file saja (tanpa path) di dalam export/
            export_dir = Path("export")
            export_dir.mkdir(parents=True, exist_ok=True)
            out_path = export_dir / Path(filename).name

            print(f"\n⚙️ Mengekspor denah ke file Excel: {out_path}...")
            stowage_list = []
            for coords, c_id in np.ndenumerate(plan):
                if c_id != 0 and c_id != 'OCCUPIED_40FT':
                    container_info, tier_id, row_index = self.container_dict[c_id], TIERS[coords[0]], coords[2]
                    bay_id_out = (BAYS[coords[1]] + 1) if container_info['size'] == 40 else BAYS[coords[1]]
                    bay_str, tier_str, row_str = f"{bay_id_out:02d}", f"{tier_id:02d}", f"{row_index:02d}"
                    stowage_list.append({
                        'Container_ID': c_id,
                        'Weight_ton': container_info['weight']/1000,
                        'Bay': bay_str,
                        'Row': row_str,
                        'Tier': tier_str,
                        'slot': f"{bay_str}{row_str}{tier_str}",
                        'Load Port': 'IDJKT',
                        'Discharge Port': 'IDSUB',
                        'Container ISO': '45G1' if container_info['size'] == 40 else '22G1',
                        'F/E': 'F'
                    })
            if stowage_list:
                df_export = pd.DataFrame(stowage_list).sort_values(by=['Bay', 'Row', 'Tier'])
                final_order = ['Container_ID', 'Bay', 'Row', 'Tier', 'slot', 'Load Port', 'Discharge Port', 'Container ISO', 'F/E', 'Weight_ton']
                df_export[final_order].to_excel(out_path, index=False)
                print(f"✅ Berhasil! Denah muatan telah disimpan sebagai '{out_path}'.")
            else:
                print("⚠️ Tidak ada kontainer untuk diekspor.")
        except Exception as e:
            print(f"❌ Gagal mengekspor ke Excel: {e}")


# MARK: Final
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
            all_containers=all_containers, lightship_data=lightship_properties, tanks_data=tanks_data,
            slot_properties_20ft=SLOT_PROPERTIES_20FT, valid_mask_20ft=VALID_SLOT_MASK_20FT,
            valid_placements_40ft=VALID_PLACEMENTS_40FT, slot_properties_40ft=SLOT_PROPERTIES_40FT,
            target_lcg=target_lcg_value
        )
        best_plan, best_summary = stowage_planner.run()
        
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
            stowage_planner.export_plan_to_excel(best_plan, "Hasil_Stowage_Plan_Final.xlsx")
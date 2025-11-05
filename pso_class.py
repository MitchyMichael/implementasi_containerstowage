from collections import defaultdict
import numpy as np
import pandas as pd
import copy
import random

class PSO_Stowage_Planner:
    """Kelas utama untuk menjalankan algoritma PSO untuk Stowage Planning."""
    def __init__(self, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, 
                    all_containers, lightship_data, tanks_data, 
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

    def _create_base_plan(self, TIERS):
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
        
        return self._repair_plan(base_position, TIERS)


    def _initialize_swarm(self, base_plan, NUM_PARTICLES, TIERS, WEIGHT_PENALTY):
        print("🚀 Menginisialisasi partikel...")
        for _ in range(NUM_PARTICLES):
            position = copy.deepcopy(base_plan)
            for _ in range(25):
                position = self._safe_swap(position)
            position = self._repair_plan(position, TIERS)
            fitness, summary = self._calculate_fitness(position, WEIGHT_PENALTY)
            particle = {'position': position, 'pbest_position': copy.deepcopy(position), 'pbest_fitness': fitness}
            self.swarm.append(particle)
            if fitness < self.gbest_fitness:
                self.gbest_fitness, self.gbest_position, self.gbest_summary = fitness, copy.deepcopy(position), summary
        print("Inisialisasi selesai.")

    # --- FUNGSI PERBAIKAN DENGAN ATURAN ON DECK BARU ---
    def _repair_plan(self, plan, TIERS):
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

    def _calculate_fitness(self, plan, WEIGHT_PENALTY):
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

    def run(self, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY):
        base_plan = self._create_base_plan(TIERS)
        self._initialize_swarm(base_plan, NUM_PARTICLES, TIERS, WEIGHT_PENALTY)
        print("\n--- Memulai Iterasi PSO ---")
        for i in range(MAX_ITERATIONS):
            for particle in self.swarm:
                repaired_position = self._repair_plan(self._update_particle_position(particle), TIERS)
                new_fitness, new_summary = self._calculate_fitness(repaired_position, WEIGHT_PENALTY)
                if new_fitness < particle['pbest_fitness']: particle['pbest_fitness'], particle['pbest_position'] = new_fitness, copy.deepcopy(repaired_position)
                if new_fitness < self.gbest_fitness: self.gbest_fitness, self.gbest_position, self.gbest_summary = new_fitness, copy.deepcopy(repaired_position), new_summary
            if (i + 1) % 10 == 0: print(f"Iterasi {i+1}/{MAX_ITERATIONS} | Best Fitness: {self.gbest_fitness:.2f}")
        print("\n--- Optimasi Selesai ---")
        return self.gbest_position, self.gbest_summary

    def export_plan_to_excel(self, plan, TIERS, BAYS, filename="stowage_plan.xlsx"):
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

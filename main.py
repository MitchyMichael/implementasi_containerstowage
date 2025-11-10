from formula import summarize_plan, get_containers, calculate_lcg, calculate_bestplan
from pso_class import PSO_Stowage_Planner
from ship_data import ship_data, datakondisikapal
import numpy as np

# MARK: Default Variable Value
TOTAL_VALID_SLOTS_20FT, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, SLOT_PROPERTIES_20FT, VALID_SLOT_MASK_20FT, VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY, BAYS, MAX_ROWS = ship_data()

all_containers = get_containers(TOTAL_VALID_SLOTS_20FT)
if all_containers:
    num_avail_20ft, num_avail_40ft = sum(1 for c in all_containers if c['size'] == 20), sum(1 for c in all_containers if c['size'] == 40)
    if num_avail_20ft < NUM_20FT_TO_LOAD or num_avail_40ft < NUM_40FT_TO_LOAD:
        print(f"❌ Error: Jumlah kontainer di CSV tidak mencukupi.")
        print(f"   - Butuh 20ft: {NUM_20FT_TO_LOAD}, Tersedia: {num_avail_20ft}")
        print(f"   - Butuh 40ft: {NUM_40FT_TO_LOAD}, Tersedia: {num_avail_40ft}")
    else:
        # Data kondisi kapal
        lightship_properties, tanks_data = datakondisikapal()
        target_lcg_value = calculate_lcg()

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
            calculate_bestplan(best_plan, stowage_planner, BAYS, TIERS, MAX_ROWS, VALID_SLOT_MASK_20FT)
            stowage_planner.export_plan_to_excel(best_plan, TIERS, BAYS, "Hasil_Stowage_Plan_Final.xlsx")
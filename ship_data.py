import math
import pandas as pd
import os, json, re
import json

from collections import defaultdict
from container_data import count_containers, read_container_array
from formula import build_ship_geometry, build_40ft_slots
from pathlib import Path

# MARK: Read Ship All
def read_ship_xlsx_all(expected_sheets: list[str] | None = None,
                    lowercase_headers: bool = True,
                    include_sheet_col: bool = True):
    """
    Gunakan read_ship_xlsx(...) untuk baca semua sheet,
    lalu kembalikan:
    - data_by_sheet: dict {sheet_name: [row_dict, ...]}
    - data_flat: list gabungan semua baris dari semua sheet.
    """
    data_by_sheet = read_ship_xlsx(expected_sheets=expected_sheets,
                                lowercase_headers=lowercase_headers)

    # Coerce angka & flatten
    data_flat = []
    for sheet_name, rows in data_by_sheet.items():
        rows = _coerce_numbers_in_records(rows)
        for r in rows:
            if include_sheet_col and "__sheet__" not in r:
                r = dict(r)
                r["__sheet__"] = sheet_name
            data_flat.append(r)

    debugexport_txtfile(data_by_sheet)
    
    rbays = []
    rtiers = []
    rrows = []
    rslots = []
    rtanks = []

    for sheet_name, data in data_by_sheet.items():
        if sheet_name.lower() == "bays":
            rbays = data
        elif sheet_name.lower() == "tiers":
            rtiers = data
        elif sheet_name.lower() == "rows":
            rrows = data
        elif sheet_name.lower() == "slots":
            rslots = data
            
            new_slots = []
            for item in rslots:
                new_slots.append({
                    "bay": item['bay'],
                    "tier": item['tier'],
                    'row': item['row'],
                    'link slot': item['link slot'],
                    'link bay': item['link bay']
                })
                
            rslots = new_slots
        elif sheet_name.lower() == "tanks":
            rtanks = data
            
    return rbays, rtiers, rrows, rslots, rtanks

def _coerce_numbers_in_records(rows: list[dict]) -> list[dict]:
    """Coba konversi string numerik ke angka (int/float) agar data lebih bersih."""
    def to_number(v):
        if isinstance(v, str):
            s = v.strip().replace(",", "")  # buang koma pemisah ribuan
            if s == "":
                return v
            try:
                # coba int dulu agar '12' tidak jadi 12.0
                i = int(s)
                return i
            except ValueError:
                try:
                    f = float(s)
                    return f
                except ValueError:
                    return v
        return v

    out = []
    for r in rows:
        out.append({k: to_number(v) for k, v in r.items()})
    return out

# MARK: Export ship data to txt (for debug)
def debugexport_txtfile(by_sheet):
    export_dir = Path("export/debug_txt")
    export_dir.mkdir(parents=True, exist_ok=True)

    def safe_name(name: str) -> str:
        # Ganti karakter yang tidak aman untuk nama file
        return re.sub(r'[^\w\-. ]+', '_', name)

    for sheet_name, data in by_sheet.items():
        filename = export_dir / f"{safe_name(sheet_name)}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        # print(f"✅ {filename} berhasil dibuat.")

# MARK: Read Ship XLSX
def read_ship_xlsx(expected_sheets: list[str] | None = None,
                        lowercase_headers: bool = True) -> dict[str, list[dict]]:
    """
    Baca semua sheet dari ./archive/ship_slot.xlsx
    Return: { "Sheet1": [ {col: val, ...}, ... ], "Sheet2": [...], ... }

    - expected_sheets: jika diisi, fungsi akan validasi nama sheet wajib ada.
    - lowercase_headers: jika True, header akan dinormalisasi ke huruf kecil & strip spasi.
    """
    file_path = "./archive/ship_slot.xlsx"

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

    # Baca semua sheet (dict of DataFrame)
    # sheet_name=None => {sheet_name: DataFrame}
    xl: dict[str, pd.DataFrame] = pd.read_excel(file_path, sheet_name=None)

    if expected_sheets:
        missing = [s for s in expected_sheets if s not in xl]
        if missing:
            raise ValueError(f"Sheet berikut tidak ditemukan: {missing}. "
                            f"Sheet yang ada: {list(xl.keys())}")

    result: dict[str, list[dict]] = {}
    for name, df in xl.items():
        # Bersihkan header kolom
        df.columns = df.columns.astype(str).str.strip()
        if lowercase_headers:
            df.columns = df.columns.str.lower()

        # Drop baris kosong total (semua NaN)
        df = df.dropna(how="all")

        # Opsional: trim string cells
        for c in df.select_dtypes(include=["object"]).columns:
            df[c] = df[c].astype(str).str.strip()

        result[name] = df.to_dict(orient="records")

    print(f"📄 File memuat {len(xl)} sheet: {list(xl.keys())}")
    total_rows = sum(len(v) for v in result.values())
    print(f"📦 Total baris dari semua sheet: {total_rows}")
    return result

def build_ship_layout(slots, BAY_MAP, TIER_MAP, ROW_INDEX):
    """
    slots: list of dict, misalnya tiap item:
        {'bay': 1, 'tier': 2, 'row': 8, ...}
    atau sesuaikan nama kolom dari Excel/DB kamu.
    """
    layout = defaultdict(lambda: defaultdict(set))

    for s in slots:
        bay_id = int(s["bay"])   # sesuaikan key dengan data kamu, mis. 'bay id'
        tier_id = int(s["tier"]) # atau 'tier id'
        row_id = int(s["row"])   # atau 'row id'

        # Lewatkan bay/tier yang tidak ada di MAP (kalau mau strict)
        if bay_id not in BAY_MAP or tier_id not in TIER_MAP or row_id not in ROW_INDEX:
            continue

        row_index = ROW_INDEX[row_id]   # 0..8
        layout[bay_id][tier_id].add(row_index)

    # 2) Konversi set → sorted list, defaultdict → dict biasa
    ship_layout = {
        bay: {tier: sorted(rows) for tier, rows in tiers.items()}
        for bay, tiers in layout.items()
    }
    return ship_layout

def find_allowed40ftbays(slots):
    allowed = set()
    invalid = set()
    for slot in slots:
        bay = slot['bay']
        row = slot['row']
        tier = slot['tier']
        link_bay = slot['link bay']
        link_slot = slot['link slot']
        if not math.isnan(link_slot):
            calculated = (bay + link_bay) / 2
            allowed.add(calculated)  
        else:
            invalid.add((
                bay, tier, row
            ))
    list_allowed = sorted(list(allowed))
    return list_allowed, invalid

# MARK: Default - Data Fisik Kapal
def ship_data():
    # ===============================================================================================================================================
    bays, tiers, rows, slots, tanks = read_ship_xlsx_all(expected_sheets=["Bays", "Tiers", "Rows", "Slots", "Tanks"])
    containers = read_container_array("./archive/container.xlsx")

    # --- Data Fisik Kapal ---
    # Bay dari midship, negatif depan, positif belakang
    BAY_MAP = {int(b['name'].strip().split()[-1]): round(b['base lcg - midship'], 3) for b in bays}
    TIER_MAP = {int(t['name'].strip().split()[-1]): round((t['base vcg']/1000), 3) for t in tiers}
    ROW_MAP = {int(r['name']): round((r['base tcg']/1000), 3) for r in rows}

    BAYS = sorted(list(BAY_MAP.keys()))
    TIERS = sorted(list(TIER_MAP.keys()))
    MAX_ROWS = len(rows)
    
    sorted_rows = sorted(ROW_MAP.items(), key=lambda kv: kv[1])  # sort by koordinat
    ROW_INDEX = {row_id: idx for idx, (row_id, _) in enumerate(sorted_rows)}

    # MARK: Data Final Tata Letak Kapal
    # ==================================================================================================================================================================================================================================================================================================================================================
    # --- Data Final Tata Letak Kapal (Struktur 20ft) ---
    SHIP_LAYOUT = build_ship_layout(slots, BAY_MAP, TIER_MAP, ROW_INDEX)

    # MARK: Aturan Khusus Kontainer 40ft
    # ==============================================================================================================================================================================
    # --- ATURAN KHUSUS UNTUK KONTAINER 40 KAKI ---
    ALLOWED_40FT_BAYS, INVALID_40FT_SLOTS = find_allowed40ftbays(slots)

    # --- KONFIGURASI DAN EKSEKUSI ---
    VALID_SLOT_MASK_20FT, SLOT_PROPERTIES_20FT = build_ship_geometry(TIERS, BAYS, MAX_ROWS, SHIP_LAYOUT, ROW_MAP, BAY_MAP, TIER_MAP)
    VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT = build_40ft_slots(VALID_SLOT_MASK_20FT, SLOT_PROPERTIES_20FT, BAYS, ALLOWED_40FT_BAYS, TIERS, INVALID_40FT_SLOTS)
    TOTAL_VALID_SLOTS_20FT, TOTAL_VALID_SLOTS_40FT = len(SLOT_PROPERTIES_20FT), len(VALID_PLACEMENTS_40FT)

    # --- KONFIGURASI ALGORITMA ---
    NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD = count_containers(containers)
    NUM_PARTICLES, MAX_ITERATIONS = 50, 200
    WEIGHT_PENALTY = {"vertical_moment": 0.0001, "longitudinal_balance": 100.0, "stability_tcg": 8000.0}
    
    return TOTAL_VALID_SLOTS_20FT, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, SLOT_PROPERTIES_20FT, VALID_SLOT_MASK_20FT, VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY, BAYS, MAX_ROWS, tanks

# MARK: Data Kondisi Kapal
def datakondisikapal(tanks):
    lightship_data = tanks[0]
    lightship_properties = {
        'weight': lightship_data['lightship weight'],
        'lcg': lightship_data['lightship lcg'],
        'vcg': lightship_data['lightship vcg'],
        'tcg': lightship_data['lightship tcg']
    }
    
    tanks_data = []
    for item in tanks:
        tanks_data.append({
            'name': item['name'],
            'weight': item['weight'],
            'lcg': item['lcg'],
            'vcg': item['vcg'],
            'tcg': item['tcg']
        })
    
    return lightship_properties, tanks_data
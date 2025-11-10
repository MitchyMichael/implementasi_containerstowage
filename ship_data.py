import math
import pandas as pd
import os, json, re
import json

from collections import defaultdict
from container_data import read_container_array
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
            
    return rbays, rtiers, rrows, rslots

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
    bays, tiers, rows, slots = read_ship_xlsx_all(expected_sheets=["Bays", "Tiers", "Rows", "Slots"])
    containers = read_container_array("./archive/container.xlsx")
    
    # print("")
    # print("Bay 1")
    # print(bays[0])
    # Bay 1
    # {'no.': 1, 'bay id': 130, 'ship id': 2004, 'name': 'Bay 01', 'prev. bay id': 131, 'dist. to prev.': 0, 'next bay id': 131, 'dist. to next': 76, 'link bay id': 131, 'dist. to link': 0, 'inhold': True, 'base lcg': 126158, 'p': 6.23999977111816, 'l': 0, 'path': 'file:/C:/Users/ISTOW/iStowV2/assets/images//2004_MVPranalaContainerX_bay 1.png'}

    # print("")
    # print("Tier 1")
    # print(tiers[0])
    # Tier 1
    # {'no.': 1, 'tier id': 82, 'ship id': 2004, 'name': 'TIER 02', 'inhold': True, 'base vcg': 1532, 'max height': 10652, 'path': 'file:/C:/Users/ISTOW/iStowV2/assets/images//2004_MVPranalaContainerX_tier-on-hold.png', 'break bulk': False, 'special desk': False, 'overwrite': 0, 'p': 119, 'bottom tier id': 0, 'bottom tier': nan, 'top tier id': 0, 'top tier': nan, 'list slot': nan}

    # print("")
    # print("Row 1")
    # print(rows[0])
    # Row 1
    # {'no.': 1, 'row id': 151, 'ship id': 2004, 'name': 8, 'base tcg': -8853}

    # print("")
    # print("Slot 1")
    # print(slots[0])
    # Slot 1
    # {'no.': 'Container', 'slot id': '1', 'bay': '0', 'row': 'nan', 'tier': 'nan', 'link bay': 'nan', 'link row': 'nan', 'link tier': 'nan', 'bottom bay': 'nan', 'bottom row': 'nan', 'bottom tier': 'nan', 'link slot': 'nan', 'bottom slot': 'nan', 'top slot': 'nan', 'left slot': 'nan', 'right slot': 'nan', 'front slot': 'nan', 'back slot': 'nan', 'segregation slot': 'nan', 'offset blcg': '0', 'offset bvcg': '2804', 'offset btcg': '0', 'rotated': 'False', 'p': '6058', 'l': '2438', 't': '2591'}

    # print("")
    # print("Banyak Container", len(containers))
    # print(containers[:1])  
    # Banyak Container 100
    # [{'no': 1, 'booking_no': nan, 'container_id': nan, 'bay': None, 'row': None, 'tier': None, 'slot': nan, 'load_port': 'IDSUB', 'discharge_port': 'IDJKT', 'container_iso': 2000, 'size_ft': 20, 'fe': 'F', 'weight_vgm_kg': 10.0, 'weight_ton': 0.01, 'un_no': None, 'dg_class': nan, 'group_type': nan, 'over_height': None, 'oversize_left': None, 'oversize_right': None, 'oversize_front': None, 'oversize_aft': None, 'carrier': nan, 'commodity': nan, 'weight_vgm': 10}]

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
    NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD = 0, 400
    NUM_PARTICLES, MAX_ITERATIONS = 50, 200
    WEIGHT_PENALTY = {"vertical_moment": 0.0001, "longitudinal_balance": 100.0, "stability_tcg": 8000.0}
    
    return TOTAL_VALID_SLOTS_20FT, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, SLOT_PROPERTIES_20FT, VALID_SLOT_MASK_20FT, VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY, BAYS, MAX_ROWS

# MARK: Data Kondisi Kapal
def datakondisikapal():
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
    return lightship_properties, tanks_data
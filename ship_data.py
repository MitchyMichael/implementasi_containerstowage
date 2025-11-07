import pandas as pd
import os, json, re
import json

from formula import build_ship_geometry, build_40ft_slots
from pathlib import Path

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
            
    return rbays, rtiers, rrows, rslots

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
        print(f"✅ {filename} berhasil dibuat.")

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

# MARK: Default - Data Fisik Kapal
def ship_data():
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
    
    return TOTAL_VALID_SLOTS_20FT, NUM_20FT_TO_LOAD, NUM_40FT_TO_LOAD, SLOT_PROPERTIES_20FT, VALID_SLOT_MASK_20FT, VALID_PLACEMENTS_40FT, SLOT_PROPERTIES_40FT, MAX_ITERATIONS, TIERS, NUM_PARTICLES, WEIGHT_PENALTY, BAYS, MAX_ROWS
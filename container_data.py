import os
import re
import math
import pandas as pd
from typing import Any, Dict, List, Tuple

def _norm_header(s: str) -> str:
    s = str(s).strip().lower()
    return re.sub(r"[^\w]+", "_", s).strip("_")

def _to_number(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    s = str(x).strip().replace(",", "").replace(" ", "")
    if s == "": return None
    try: return float(s)
    except ValueError: return None

def _parse_slot(slot: str) -> Tuple[int|None, int|None, int|None]:
    if not slot: return (None, None, None)
    s = str(slot).strip()
    if re.fullmatch(r"\d{6}", s):
        return (int(s[0:2]), int(s[2:4]), int(s[4:6]))
    parts = [p for p in re.split(r"[^0-9]+", s) if p]
    if len(parts) >= 3:
        try: return (int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError: pass
    return (None, None, None)

def _size_from_iso(iso: str|None) -> int|None:
    if not iso: return None
    s = str(iso).upper().strip()
    if s.startswith("45"): return 45
    if s[:1] == "2": return 20
    if s[:1] == "4": return 40
    m = re.match(r"^(20|40|45)", s)
    return int(m.group(1)) if m else None

# MARK: Read Container Array
def read_container_array(file_path: str = "container.xlsx") -> List[Dict[str, Any]]:
    """Baca container.xlsx (sheet pertama) -> list[dict]"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File tidak ditemukan: {file_path}")

    df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
    df.columns = [_norm_header(c) for c in df.columns]
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

    # Pemetaan kolom ke nama konsisten
    colmap = {
        "no": "no",
        "booking_no": "booking_no",
        "container_id": "container_id",
        "bay": "bay", "row": "row", "tier": "tier",
        "slot": "slot",
        "load_port": "load_port",
        "discharge_port": "discharge_port",
        "container_iso": "container_iso",
        "f_e": "fe",                # F/E
        "weight_vgm": "weight_vgm", # header "Weight (VGM)" -> jadi weight_vgm saat dinormalisasi
        "un_no": "un_no",
        "dg_class": "dg_class",
        "group_type": "group_type",
        "over_height": "over_height",
        "over_size_left": "oversize_left",
        "over_size_right": "oversize_right",
        "over_size_front": "oversize_front",
        "over_size_aft": "oversize_aft",
        "carrier": "carrier",
        "commodity": "commodity",
    }
    df = df.rename(columns={k: v for k, v in colmap.items() if k in df.columns})

    # Minimal harus ada container_id
    if "container_id" not in df.columns:
        raise ValueError(f"Kolom 'Container ID' tidak ditemukan. Kolom tersedia: {list(df.columns)}")

    # Bersihkan string
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].astype(str).str.strip().replace({"nan": None})

    # Konversi numerik umum
    for c in ("bay", "row", "tier", "un_no", "over_height",
            "oversize_left", "oversize_right", "oversize_front", "oversize_aft"):
        if c in df.columns:
            df[c] = df[c].apply(_to_number)

    # Weight (VGM) → kg & ton
    if "weight_vgm" in df.columns:
        df["weight_vgm_kg"] = df["weight_vgm"].apply(_to_number)
        df["weight_ton"] = df["weight_vgm_kg"].apply(lambda v: None if v is None else v / 1000.0)

    # Isi bay/row/tier dari Slot jika kosong
    if "slot" in df.columns:
        def fill_brt(row):
            b, r, t = row.get("bay"), row.get("row"), row.get("tier")
            if (b is None or r is None or t is None) and row.get("slot"):
                pb, pr, pt = _parse_slot(row["slot"])
                b = b if b is not None else pb
                r = r if r is not None else pr
                t = t if t is not None else pt
            return pd.Series({"bay": b, "row": r, "tier": t})
        brt = df.apply(fill_brt, axis=1)
        for c in ("bay", "row", "tier"):
            df[c] = brt[c]

    # Derive size_ft dari ISO
    if "container_iso" in df.columns:
        df["size_ft"] = df["container_iso"].apply(_size_from_iso)

    # NaN -> None
    df = df.where(pd.notnull(df), None)

    # Urutan kolom enak dibaca (opsional)
    order = [
        "no", "booking_no", "container_id",
        "bay", "row", "tier", "slot",
        "load_port", "discharge_port",
        "container_iso", "size_ft", "fe",
        "weight_vgm_kg", "weight_ton",
        "un_no", "dg_class", "group_type",
        "over_height", "oversize_left", "oversize_right", "oversize_front", "oversize_aft",
        "carrier", "commodity",
    ]
    cols = [c for c in order if c in df.columns] + [c for c in df.columns if c not in order]
    df = df[cols]

    return df.to_dict(orient="records")

def count_containers(containers):
    # print("")
    # print("Banyak Container", len(containers))
    # print(containers[:1])  
    # Banyak Container 100
    # [{'no': 1, 'booking_no': nan, 'container_id': nan, 'bay': None, 'row': None, 'tier': None, 'slot': nan, 'load_port': 'IDSUB', 'discharge_port': 'IDJKT', 'container_iso': 2000, 'size_ft': 20, 'fe': 'F', 'weight_vgm_kg': 10.0, 'weight_ton': 0.01, 'un_no': None, 'dg_class': nan, 'group_type': nan, 'over_height': None, 'oversize_left': None, 'oversize_right': None, 'oversize_front': None, 'oversize_aft': None, 'carrier': nan, 'commodity': nan, 'weight_vgm': 10}]
    
    count_20ft = 0
    count_40ft = 0
    for item in containers:
        iso = int(str(item['container_iso'])[0])
        if iso == 2:
            count_20ft += 1
        elif iso == 4:
            count_40ft += 1
    return count_20ft, count_40ft

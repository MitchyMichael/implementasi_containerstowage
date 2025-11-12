import os
import re
import pandas as pd

def extract_size_from_iso(iso_value: str | int | float) -> int | None:
    """
    Ambil digit pertama dari string ISO, map:
    '2' -> 20, '4' -> 40
    Selain itu -> None (atau bisa kamu map sesuai kebutuhan).
    """
    if pd.isna(iso_value):
        return None
    s = str(iso_value).strip()
    m = re.search(r'\d', s)
    if not m:
        return None
    first_digit = m.group()
    if first_digit == '2':
        return 20
    if first_digit == '4':
        return 40
    return None  # jika ingin aturan lain, ubah di sini

def to_two_decimal_if_number(x):
    # opsional: jika ingin membulatkan tampilan angka; saat ini biarkan apa adanya
    return x

def build_container_id(i: int) -> str:
    # CONT0001, CONT0002, ...
    return f"CONT{i:04d}"

def make_csv_from_excel(
    xlsx_path: str = "./archive/container.xlsx",
    out_csv_path: str = "./export/containers_mapped.csv",
    sheet_name: str | int | None = 0  # default sheet pertama
):
    # Baca Excel
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)

    # Normalisasi header agar tahan perbedaan kapitalisasi/spasi
    rename_map = {c: c.strip().lower() for c in df.columns}
    df.columns = [rename_map[c] for c in df.columns]

    # Nama kolom yang dibutuhkan (setara)
    col_iso = next((c for c in df.columns if c in ["container iso", "container_iso", "containeriso"]), None)
    col_vgm = next((c for c in df.columns if c in ["weight (vgm)", "weight_vgm", "weight vgm", "vgm"]), None)

    if col_iso is None or col_vgm is None:
        raise ValueError(
            f"Kolom wajib tidak ditemukan. Ditemukan kolom: {list(df.columns)}. "
            "Pastikan ada 'Container ISO' dan 'Weight (VGM)'."
        )

    # Bangun output
    out = pd.DataFrame()
    out["Container_ID"] = [build_container_id(i+1) for i in range(len(df))]
    out["Weight_ton"]   = df[col_vgm].astype(float)  # sesuai permintaan: 'sesuai weight vgm'
    out["Size"]         = df[col_iso].apply(extract_size_from_iso)

    # (opsional) validasi Size None
    if out["Size"].isna().any():
        missing = out[out["Size"].isna()].index.tolist()
        print(f"Peringatan: {len(missing)} baris tidak dapat ditentukan Size dari 'Container ISO'.")

    # Pastikan folder export ada
    os.makedirs(os.path.dirname(out_csv_path), exist_ok=True)

    # Tulis CSV tanpa index
    out.to_csv(out_csv_path, index=False)

    print(f"✅ CSV berhasil dibuat: {out_csv_path}")
    return out_csv_path, out

# ==== Cara pakai ====
# path, df_out = make_csv_from_excel("./archive/container.xlsx", "./export/containers_mapped.csv")

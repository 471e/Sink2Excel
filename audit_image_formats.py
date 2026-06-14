import argparse
import csv
from pathlib import Path


DEFAULT_ROOTS = [
    Path(r"C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto KTP (File responses)"),
    Path(r"C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto Rumah (File responses)"),
    Path(r"C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto Meter Listrik (File responses)"),
]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Audit format asli file gambar dari header/magic bytes."
    )
    parser.add_argument(
        "roots",
        nargs="*",
        help="Folder yang ingin discan. Jika kosong, pakai folder default."
    )
    parser.add_argument(
        "--output",
        default="laporan_format_gambar.csv",
        help="Path CSV output laporan audit."
    )
    return parser.parse_args()


def detect_actual_format(file_path):
    try:
        data = file_path.read_bytes()[:32]
    except Exception as exc:
        return "unreadable", str(exc)

    if len(data) < 12:
        return "too_small", "Ukuran file terlalu kecil untuk diidentifikasi."

    if data[:3] == b"\xff\xd8\xff":
        return "jpeg", ""
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", ""
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", ""
    if data[4:8] == b"ftyp":
        brand = data[8:12].decode("latin1", "ignore").lower()
        if brand in {"heic", "heix", "hevc", "hevx", "mif1", "msf1"}:
            return "heic", ""
        if brand == "avif":
            return "avif", ""
        return f"iso-bmff:{brand}", ""

    return "unknown", "Header file tidak dikenali."


def map_expected_format(extension):
    mapping = {
        ".jpg": "jpeg",
        ".jpeg": "jpeg",
        ".png": "png",
        ".heic": "heic",
        ".heif": "heic",
        ".webp": "webp",
    }
    return mapping.get(extension.lower(), "unknown")


def build_status(extension, actual_format):
    expected_format = map_expected_format(extension)
    if actual_format in {"unreadable", "too_small", "unknown"}:
        return "perlu_cek"
    if expected_format == actual_format:
        return "ok"
    return "ekstensi_tidak_sesuai"


def iter_image_files(root):
    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
            yield file_path


def audit_root(root):
    rows = []
    for file_path in iter_image_files(root):
        actual_format, note = detect_actual_format(file_path)
        status = build_status(file_path.suffix, actual_format)
        rows.append(
            {
                "folder": str(root),
                "relative_path": str(file_path.relative_to(root)),
                "file_name": file_path.name,
                "extension": file_path.suffix.lower(),
                "actual_format": actual_format,
                "status": status,
                "size_bytes": file_path.stat().st_size,
                "note": note,
            }
        )
    return rows


def main():
    args = parse_args()
    roots = [Path(path) for path in args.roots] if args.roots else DEFAULT_ROOTS

    invalid_roots = [str(path) for path in roots if not path.is_dir()]
    if invalid_roots:
        raise FileNotFoundError(
            "Folder tidak ditemukan:\n" + "\n".join(invalid_roots)
        )

    all_rows = []
    for root in roots:
        all_rows.extend(audit_root(root))

    output_path = Path(args.output)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "folder",
                "relative_path",
                "file_name",
                "extension",
                "actual_format",
                "status",
                "size_bytes",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    mismatch_count = sum(1 for row in all_rows if row["status"] != "ok")
    print("Audit selesai.")
    print(f"Total file  : {len(all_rows)}")
    print(f"Perlu cek   : {mismatch_count}")
    print(f"CSV output  : {output_path.resolve()}")


if __name__ == "__main__":
    main()

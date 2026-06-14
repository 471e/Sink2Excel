import argparse
import csv
from pathlib import Path

from audit_image_formats import DEFAULT_ROOTS, detect_actual_format


TARGET_EXTENSIONS = {".jpg", ".jpeg"}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Perbaiki file .jpg/.jpeg yang sebenarnya berformat HEIC."
    )
    parser.add_argument(
        "roots",
        nargs="*",
        help="Folder yang ingin diperiksa. Jika kosong, pakai folder default."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Terapkan rename file. Default hanya simulasi."
    )
    parser.add_argument(
        "--output",
        default="rencana_perbaikan_heic.csv",
        help="Path CSV output untuk hasil scan/perbaikan."
    )
    return parser.parse_args()


def iter_candidate_files(root):
    for file_path in sorted(root.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in TARGET_EXTENSIONS:
            yield file_path


def build_target_path(file_path):
    return file_path.with_suffix(".heic")


def inspect_file(file_path):
    actual_format, note = detect_actual_format(file_path)
    if actual_format != "heic":
        return None

    target_path = build_target_path(file_path)
    if target_path.exists():
        action = "skip_target_exists"
    else:
        action = "rename_to_heic"

    return {
        "folder": str(file_path.parent),
        "old_name": file_path.name,
        "new_name": target_path.name,
        "old_path": str(file_path),
        "new_path": str(target_path),
        "actual_format": actual_format,
        "size_bytes": file_path.stat().st_size,
        "action": action,
        "status": "planned",
        "note": note,
    }


def main():
    args = parse_args()
    roots = [Path(path) for path in args.roots] if args.roots else DEFAULT_ROOTS

    invalid_roots = [str(path) for path in roots if not path.is_dir()]
    if invalid_roots:
        raise FileNotFoundError(
            "Folder tidak ditemukan:\n" + "\n".join(invalid_roots)
        )

    plans = []
    renamed_count = 0
    skipped_count = 0

    for root in roots:
        for file_path in iter_candidate_files(root):
            plan = inspect_file(file_path)
            if not plan:
                continue

            if args.apply and plan["action"] == "rename_to_heic":
                Path(plan["old_path"]).rename(plan["new_path"])
                plan["status"] = "renamed"
                renamed_count += 1
            elif args.apply:
                plan["status"] = "skipped"
                skipped_count += 1
            else:
                plan["status"] = "dry_run"

            plans.append(plan)

    output_path = Path(args.output)
    with output_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "folder",
                "old_name",
                "new_name",
                "old_path",
                "new_path",
                "actual_format",
                "size_bytes",
                "action",
                "status",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(plans)

    print("Periksa mislabeled HEIC selesai.")
    print(f"Total kandidat : {len(plans)}")
    print(f"Mode           : {'apply' if args.apply else 'dry-run'}")
    print(f"CSV output     : {output_path.resolve()}")
    if args.apply:
        print(f"Berhasil rename: {renamed_count}")
        print(f"Dilewati       : {skipped_count}")


if __name__ == "__main__":
    main()

import argparse
import os

from sync_core import (
    DEFAULT_FOLDER_PATHS,
    FOTO_COLUMNS,
    REQUIRED_FOTO_COLUMNS,
    build_file_maps,
    build_log_row,
    build_output_filename,
    format_counts_summary,
    get_matching_sheets,
    load_all_sheet_data,
    resolve_active_foto_columns,
    save_workbook,
    sync_dataframe,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sinkronisasi path file gambar ke kolom Excel."
    )
    parser.add_argument(
        "excel_path",
        nargs="?",
        default="data.xlsx",
        help="Path file Excel sumber."
    )
    parser.add_argument(
        "--sheet",
        help="Nama sheet tertentu yang ingin diproses."
    )
    parser.add_argument(
        "--all-sheets",
        action="store_true",
        help="Proses semua sheet yang memiliki kolom foto wajib."
    )
    parser.add_argument(
        "--foto-ktp",
        help="Folder lokal untuk kolom Foto KTP."
    )
    parser.add_argument(
        "--foto-rumah",
        help="Folder lokal untuk kolom Foto Rumah."
    )
    parser.add_argument(
        "--foto-meter-listrik",
        help="Folder lokal untuk kolom Foto Meter Listrik."
    )
    parser.add_argument(
        "--foto-lainnya",
        help="Folder lokal untuk kolom Foto Lainnya."
    )
    parser.add_argument(
        "--use-default-folders",
        action="store_true",
        help="Gunakan path folder default yang sudah diisi di script."
    )
    parser.add_argument(
        "--output",
        help="Path file output Excel."
    )
    return parser.parse_args()

def resolve_folder_paths(args):
    folder_paths = {
        "Foto KTP": args.foto_ktp,
        "Foto Rumah": args.foto_rumah,
        "Foto Meter Listrik": args.foto_meter_listrik,
        "Foto Lainnya": args.foto_lainnya,
    }

    if args.use_default_folders:
        folder_paths.update(DEFAULT_FOLDER_PATHS)

    missing_columns = [
        col for col in REQUIRED_FOTO_COLUMNS if not folder_paths.get(col)
    ]
    if missing_columns:
        raise ValueError(
            "Folder gambar wajib diisi untuk kolom: " + ", ".join(missing_columns)
        )

    invalid_paths = [
        f"{col}: {path}" for col, path in folder_paths.items() if not os.path.isdir(path)
    ]
    if invalid_paths:
        raise ValueError(
            "Folder gambar tidak ditemukan:\n" + "\n".join(invalid_paths)
        )

    return folder_paths


def select_target_sheets(excel_path, requested_sheet, process_all):
    matching_sheets = get_matching_sheets(excel_path, REQUIRED_FOTO_COLUMNS)
    if not matching_sheets:
        raise ValueError(
            "Tidak ada sheet Excel yang memiliki kolom: "
            + ", ".join(REQUIRED_FOTO_COLUMNS)
        )

    if requested_sheet:
        if requested_sheet not in matching_sheets:
            raise ValueError(
                f"Sheet '{requested_sheet}' tidak valid. Pilihan yang tersedia: "
                + ", ".join(matching_sheets)
            )
        return [requested_sheet]

    if process_all:
        return matching_sheets

    return [matching_sheets[0]]


def main():
    args = parse_args()
    excel_path = args.excel_path

    if not os.path.isfile(excel_path):
        raise FileNotFoundError(f"File Excel tidak ditemukan: {excel_path}")

    folder_paths = resolve_folder_paths(args)
    target_sheets = select_target_sheets(excel_path, args.sheet, args.all_sheets)
    files_by_column = build_file_maps(folder_paths)
    all_sheets = load_all_sheet_data(excel_path)

    processed_sheets = []
    log_rows = []
    mismatch_details = []
    total_matches = 0

    for sheet_name in target_sheets:
        active_foto_columns = resolve_active_foto_columns(
            all_sheets[sheet_name],
            folder_paths
        )
        synced_df, stats, sheet_mismatches = sync_dataframe(
            all_sheets[sheet_name].copy(),
            files_by_column,
            sheet_name,
            active_foto_columns,
        )
        all_sheets[sheet_name] = synced_df
        processed_sheets.append((sheet_name, stats))
        log_rows.append(build_log_row(sheet_name, stats, active_foto_columns))
        mismatch_details.extend(sheet_mismatches)
        total_matches += sum(item["matched"] for item in stats.values())

    output_path = args.output
    if not output_path:
        mode_label = "semua_sheet_valid" if len(target_sheets) > 1 else "sheet_terpilih"
        selected_sheet = None if len(target_sheets) > 1 else target_sheets[0]
        output_path = build_output_filename(excel_path, mode_label, selected_sheet)

    save_workbook(
        all_sheets,
        output_path,
        log_rows=log_rows,
        mismatch_details=mismatch_details
    )

    print("Sinkronisasi selesai.")
    print(f"File output : {output_path}")
    print(f"Total cocok : {total_matches}")
    print(f"Total sheet : {len(target_sheets)}")
    print("Ringkasan:")
    for sheet_name, stats in processed_sheets:
        print(f"- {sheet_name}: {format_counts_summary(stats)}")

    if mismatch_details:
        print(f"Total tidak cocok: {len(mismatch_details)}")
    else:
        print("Tidak ada mismatch.")


if __name__ == "__main__":
    main()

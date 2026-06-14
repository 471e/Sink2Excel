import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
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
    load_sheet_data,
    resolve_active_foto_columns,
    save_workbook,
    sync_dataframe,
)


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class SyncApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sinkronisasi File Gambar dengan Excel")
        self.root.geometry("720x520")
        self.foto_columns = FOTO_COLUMNS
        self.required_foto_columns = REQUIRED_FOTO_COLUMNS
        self.sheet_options = []
        self.folder_paths = {col: None for col in self.foto_columns}
        self.folder_labels = {}
        self.last_saved_path = None
        self.automation = self.load_automation_settings()

        # Label dan tombol untuk pilih file Excel
        self.label_excel = tk.Label(root, text="Pilih file Excel:")
        self.label_excel.pack(pady=5)
        self.btn_excel = tk.Button(root, text="Browse Excel", command=self.load_excel)
        self.btn_excel.pack(pady=5)
        self.excel_path = None

        # Pilihan sheet valid dari file Excel
        self.label_sheet = tk.Label(root, text="Sheet Excel:")
        self.label_sheet.pack(pady=5)
        self.sheet_var = tk.StringVar(value="Pilih file Excel terlebih dahulu")
        self.sheet_combo = ttk.Combobox(
            root,
            textvariable=self.sheet_var,
            state="disabled",
            width=45
        )
        self.sheet_combo.pack(pady=5)

        # Label dan tombol untuk pilih folder gambar per kolom foto
        self.label_folder = tk.Label(root, text="Pilih folder gambar per kolom:")
        self.label_folder.pack(pady=5)

        for col in self.foto_columns:
            frame = tk.Frame(root)
            frame.pack(fill="x", padx=20, pady=4)

            btn = tk.Button(
                frame,
                text=f"Browse {col}",
                command=lambda column=col: self.load_folder(column)
            )
            btn.pack(side="left")

            label = tk.Label(frame, text=f"{col}: belum dipilih", anchor="w")
            label.pack(side="left", padx=10)
            self.folder_labels[col] = label

        self.folder_action_frame = tk.Frame(root)
        self.folder_action_frame.pack(pady=10)
        self.btn_default_folder = tk.Button(
            self.folder_action_frame,
            text="Isi Folder Default",
            command=self.load_default_folders
        )
        self.btn_default_folder.pack(side="left", padx=6)
        self.btn_reset_folder = tk.Button(
            self.folder_action_frame,
            text="Reset Folder",
            command=self.reset_folders
        )
        self.btn_reset_folder.pack(side="left", padx=6)

        # Tombol aksi sinkronisasi
        self.sync_action_frame = tk.Frame(root)
        self.sync_action_frame.pack(pady=20)
        self.btn_sync = tk.Button(
            self.sync_action_frame,
            text="Sinkronisasi Sheet Terpilih",
            command=self.sync_selected_sheet,
            state=tk.DISABLED
        )
        self.btn_sync.pack(side="left", padx=6)
        self.btn_sync_all = tk.Button(
            self.sync_action_frame,
            text="Sinkronisasi Semua Sheet Valid",
            command=self.sync_all_sheets,
            state=tk.DISABLED
        )
        self.btn_sync_all.pack(side="left", padx=6)

        self.output_action_frame = tk.Frame(root)
        self.output_action_frame.pack(pady=5)
        self.btn_open_output_folder = tk.Button(
            self.output_action_frame,
            text="Buka Folder Hasil",
            command=self.open_output_folder,
            state=tk.DISABLED
        )
        self.btn_open_output_folder.pack(side="left", padx=6)

        # Info status
        self.status = tk.Label(root, text="", fg="green")
        self.status.pack(pady=5)

        if self.automation:
            # Tunda sedikit agar window selesai dirender sebelum workflow otomatis berjalan.
            self.root.after(300, self.run_automation_workflow)

    def load_automation_settings(self):
        if not env_flag("SYNC_APP_AUTOMATION"):
            return None

        mode = os.getenv("SYNC_APP_AUTOMATION_MODE", "selected").strip().lower()
        if mode not in {"selected", "all"}:
            raise ValueError(
                "SYNC_APP_AUTOMATION_MODE hanya mendukung 'selected' atau 'all'."
            )

        return {
            "excel_path": os.getenv("SYNC_APP_AUTOMATION_EXCEL", "").strip() or None,
            "output_path": os.getenv("SYNC_APP_AUTOMATION_OUTPUT", "").strip() or None,
            "report_path": os.getenv("SYNC_APP_AUTOMATION_REPORT", "").strip() or None,
            "mode": mode,
            "use_default_folders": env_flag(
                "SYNC_APP_AUTOMATION_USE_DEFAULT_FOLDERS", True
            ),
            "close_on_finish": env_flag("SYNC_APP_AUTOMATION_CLOSE", True),
        }

    def write_automation_report(self, status, message, **extra):
        if not self.automation or not self.automation.get("report_path"):
            return

        report_path = self.automation["report_path"]
        report_dir = os.path.dirname(report_path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)

        payload = {
            "status": status,
            "message": message,
            "excel_path": self.excel_path,
            "last_saved_path": self.last_saved_path,
            **extra,
        }

        with open(report_path, "w", encoding="utf-8") as report_file:
            json.dump(payload, report_file, indent=2, ensure_ascii=False)

    def load_excel_from_path(self, path):
        self.excel_path = path
        self.label_excel.config(text=f"File Excel: {os.path.basename(path)}")
        self.load_sheet_options()
        self.status.config(
            text=f"Ditemukan {len(self.sheet_options)} sheet yang cocok.",
            fg="green"
        )
        self.check_ready()

    def ensure_ready_for_sync(self):
        if not self.excel_path:
            raise ValueError("File Excel belum dipilih.")

        missing_folders = [
            col
            for col in self.required_foto_columns
            if not self.folder_paths.get(col) or not os.path.isdir(self.folder_paths[col])
        ]
        if missing_folders:
            raise ValueError(
                "Folder gambar belum lengkap atau tidak valid: "
                + ", ".join(missing_folders)
            )

        invalid_optional_folders = [
            col
            for col, path in self.folder_paths.items()
            if path and not os.path.isdir(path)
        ]
        if invalid_optional_folders:
            raise ValueError(
                "Folder gambar tidak valid: " + ", ".join(invalid_optional_folders)
            )

        if not self.sheet_options:
            raise ValueError("Tidak ada sheet valid yang siap diproses.")

    def prepare_save_path(self, save_path):
        output_dir = os.path.dirname(save_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        return save_path

    def run_sync_selected_sheet_automation(self, save_path):
        sheet_name, df = self.load_selected_sheet()
        files_by_column = self.build_file_maps()
        all_sheets = self.load_all_sheet_data()
        synced_df, stats, mismatch_details = self.sync_dataframe(
            df.copy(),
            files_by_column,
            sheet_name
        )
        all_sheets[sheet_name] = synced_df
        log_rows = [build_log_row(sheet_name, stats, list(stats.keys()))]
        save_path = self.prepare_save_path(save_path)
        save_workbook(
            all_sheets,
            save_path,
            log_rows=log_rows,
            mismatch_details=mismatch_details
        )
        self.set_last_saved_path(save_path)
        total_matches = sum(item["matched"] for item in stats.values())
        self.status.config(
            text=(
                f"Sheet '{sheet_name}' selesai disinkronkan "
                f"({total_matches} file cocok).\n"
                f"File disimpan di:\n{save_path}"
            ),
            fg="green"
        )
        self.write_automation_report(
            "success",
            "Sinkronisasi otomatis sheet terpilih berhasil.",
            mode="selected",
            sheet_name=sheet_name,
            total_matches=total_matches,
            stats=stats,
            mismatch_count=len(mismatch_details),
        )

    def run_sync_all_sheets_automation(self, save_path):
        files_by_column = self.build_file_maps()
        all_sheets = self.load_all_sheet_data()
        processed_sheets = 0
        total_matches = 0
        log_rows = []
        mismatch_details = []

        for sheet_name in self.sheet_options:
            synced_df, stats, sheet_mismatches = self.sync_dataframe(
                all_sheets[sheet_name].copy(),
                files_by_column,
                sheet_name
            )
            all_sheets[sheet_name] = synced_df
            processed_sheets += 1
            total_matches += sum(item["matched"] for item in stats.values())
            log_rows.append(build_log_row(sheet_name, stats, list(stats.keys())))
            mismatch_details.extend(sheet_mismatches)

        save_path = self.prepare_save_path(save_path)
        save_workbook(
            all_sheets,
            save_path,
            log_rows=log_rows,
            mismatch_details=mismatch_details
        )
        self.set_last_saved_path(save_path)
        self.status.config(
            text=(
                f"{processed_sheets} sheet valid selesai disinkronkan "
                f"({total_matches} file cocok).\n"
                f"File disimpan di:\n{save_path}"
            ),
            fg="green"
        )
        self.write_automation_report(
            "success",
            "Sinkronisasi otomatis semua sheet berhasil.",
            mode="all",
            processed_sheets=processed_sheets,
            total_matches=total_matches,
            mismatch_count=len(mismatch_details),
        )

    def run_automation_workflow(self):
        try:
            excel_path = self.automation["excel_path"]
            if not excel_path:
                raise ValueError("SYNC_APP_AUTOMATION_EXCEL wajib diisi.")
            if not os.path.isfile(excel_path):
                raise FileNotFoundError(f"File Excel tidak ditemukan: {excel_path}")

            self.load_excel_from_path(excel_path)

            if self.automation["use_default_folders"]:
                self.load_default_folders()

            self.ensure_ready_for_sync()

            if self.automation["mode"] == "all":
                save_path = (
                    self.automation["output_path"]
                    or build_output_filename(self.excel_path, "semua_sheet_valid")
                )
                self.run_sync_all_sheets_automation(save_path)
            else:
                selected_sheet = self.sheet_var.get().strip()
                save_path = (
                    self.automation["output_path"]
                    or build_output_filename(
                        self.excel_path,
                        "sheet_terpilih",
                        selected_sheet
                    )
                )
                self.run_sync_selected_sheet_automation(save_path)
        except Exception as e:
            self.status.config(text="Sinkronisasi otomatis gagal.", fg="red")
            self.write_automation_report(
                "error",
                str(e),
                mode=self.automation["mode"],
            )
        finally:
            if self.automation["close_on_finish"]:
                self.root.after(300, self.root.destroy)

    def load_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            try:
                self.load_excel_from_path(path)
            except Exception as e:
                self.sheet_options = []
                self.sheet_combo["values"] = []
                self.sheet_combo.config(state="disabled")
                self.sheet_var.set("Tidak ada sheet yang cocok")
                self.status.config(text="File Excel tidak bisa diproses.", fg="red")
                messagebox.showerror("Error", f"Terjadi kesalahan:\n{str(e)}")
            finally:
                self.check_ready()

    def load_folder(self, column_name):
        path = filedialog.askdirectory()
        if path:
            self.set_folder_path(column_name, path)
            self.check_ready()

    def set_folder_path(self, column_name, path):
        self.folder_paths[column_name] = path
        display_path = path if path else "belum dipilih"
        self.folder_labels[column_name].config(text=f"{column_name}: {display_path}")

    def load_default_folders(self):
        try:
            missing_paths = [
                f"{col}: {path}"
                for col, path in DEFAULT_FOLDER_PATHS.items()
                if not os.path.isdir(path)
            ]
            if missing_paths:
                raise ValueError(
                    "Folder default tidak ditemukan:\n" + "\n".join(missing_paths)
                )

            for col, path in DEFAULT_FOLDER_PATHS.items():
                self.set_folder_path(col, path)

            self.status.config(text="Folder default berhasil dimuat.", fg="green")
        except Exception as e:
            self.status.config(text="Folder default gagal dimuat.", fg="red")
            if not self.automation:
                messagebox.showerror("Error", f"Terjadi kesalahan:\n{str(e)}")
        finally:
            self.check_ready()

    def reset_folders(self):
        for col in self.foto_columns:
            self.set_folder_path(col, None)

        self.status.config(text="Pilihan folder sudah direset.", fg="red")
        self.check_ready()

    def check_ready(self):
        has_required_folders = all(
            self.folder_paths.get(col) for col in self.required_foto_columns
        )
        if self.excel_path and has_required_folders and self.sheet_options:
            self.btn_sync.config(state=tk.NORMAL)
            self.btn_sync_all.config(state=tk.NORMAL)
        else:
            self.btn_sync.config(state=tk.DISABLED)
            self.btn_sync_all.config(state=tk.DISABLED)

    def set_last_saved_path(self, save_path):
        self.last_saved_path = save_path
        self.btn_open_output_folder.config(
            state=tk.NORMAL if save_path else tk.DISABLED
        )

    def open_output_folder(self):
        if not self.last_saved_path:
            messagebox.showinfo("Info", "Belum ada file hasil yang disimpan.")
            return

        output_dir = os.path.dirname(self.last_saved_path)
        if not os.path.isdir(output_dir):
            messagebox.showerror(
                "Error",
                f"Folder hasil tidak ditemukan:\n{output_dir}"
            )
            return

        os.startfile(output_dir)

    def load_sheet_options(self):
        self.sheet_options = get_matching_sheets(
            self.excel_path,
            self.required_foto_columns
        )

        if not self.sheet_options:
            self.sheet_combo["values"] = []
            self.sheet_combo.config(state="disabled")
            self.sheet_var.set("Tidak ada sheet yang cocok")
            raise ValueError(
                "Tidak ada sheet Excel yang memiliki kolom: "
                + ", ".join(self.required_foto_columns)
            )

        self.sheet_combo["values"] = self.sheet_options
        self.sheet_combo.config(state="readonly")
        self.sheet_combo.current(0)

    def load_selected_sheet(self):
        selected_sheet = self.sheet_var.get().strip()
        if not selected_sheet or selected_sheet not in self.sheet_options:
            raise ValueError("Pilih sheet Excel yang ingin diproses.")

        df = load_sheet_data(self.excel_path, selected_sheet)
        return selected_sheet, df

    def load_all_sheet_data(self):
        return load_all_sheet_data(self.excel_path)

    def build_file_maps(self):
        return build_file_maps(self.folder_paths)

    def sync_dataframe(self, df, files_by_column, sheet_name):
        active_foto_columns = resolve_active_foto_columns(df, self.folder_paths)
        return sync_dataframe(
            df,
            files_by_column,
            sheet_name,
            active_foto_columns
        )

    def format_counts_summary(self, stats):
        return format_counts_summary(stats)

    def build_output_filename(self, mode_label, sheet_name=None):
        return os.path.basename(
            build_output_filename(self.excel_path, mode_label, sheet_name)
        )

    def confirm_before_save(self, title, lines):
        message = "\n".join(lines) + "\n\nLanjut simpan file?"
        return messagebox.askyesno(title, message)

    def sync_selected_sheet(self):
        try:
            sheet_name, df = self.load_selected_sheet()
            files_by_column = self.build_file_maps()
            all_sheets = self.load_all_sheet_data()
            synced_df, stats, mismatch_details = self.sync_dataframe(
                df.copy(),
                files_by_column,
                sheet_name
            )
            all_sheets[sheet_name] = synced_df
            log_rows = [build_log_row(sheet_name, stats, list(stats.keys()))]
            summary_lines = [
                f"Sheet: {sheet_name}",
                f"Total cocok: {sum(item['matched'] for item in stats.values())}",
                self.format_counts_summary(stats)
            ]

            if not self.confirm_before_save("Preview Sinkronisasi", summary_lines):
                self.status.config(text="Penyimpanan dibatalkan dari preview.", fg="red")
                return

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Simpan file Excel hasil sinkronisasi",
                initialfile=self.build_output_filename("sheet_terpilih", sheet_name),
                initialdir=os.path.dirname(self.excel_path)
            )
            if save_path:
                save_workbook(
                    all_sheets,
                    save_path,
                    log_rows=log_rows,
                    mismatch_details=mismatch_details
                )
                self.set_last_saved_path(save_path)
                self.status.config(
                    text=(
                        f"Sheet '{sheet_name}' selesai disinkronkan "
                        f"({sum(item['matched'] for item in stats.values())} file cocok).\n"
                        f"File disimpan di:\n{save_path}"
                    ),
                    fg="green"
                )
            else:
                self.status.config(text="Proses dibatalkan, file tidak disimpan.", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan:\n{str(e)}")
            self.status.config(text="Sinkronisasi gagal.", fg="red")

    def sync_all_sheets(self):
        try:
            files_by_column = self.build_file_maps()
            all_sheets = self.load_all_sheet_data()
            processed_sheets = 0
            total_matches = 0
            sheet_summaries = []
            log_rows = []
            mismatch_details = []

            for sheet_name in self.sheet_options:
                synced_df, stats, sheet_mismatches = self.sync_dataframe(
                    all_sheets[sheet_name].copy(),
                    files_by_column,
                    sheet_name
                )
                all_sheets[sheet_name] = synced_df
                processed_sheets += 1
                total_matches += sum(item["matched"] for item in stats.values())
                sheet_summaries.append(
                    f"{sheet_name}: {self.format_counts_summary(stats)}"
                )
                log_rows.append(build_log_row(sheet_name, stats, list(stats.keys())))
                mismatch_details.extend(sheet_mismatches)

            preview_lines = [
                f"Sheet valid: {processed_sheets}",
                f"Total cocok: {total_matches}",
                "Ringkasan per sheet:",
                *sheet_summaries
            ]

            if not self.confirm_before_save("Preview Semua Sheet", preview_lines):
                self.status.config(text="Penyimpanan dibatalkan dari preview.", fg="red")
                return

            save_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx *.xls")],
                title="Simpan file Excel hasil semua sheet",
                initialfile=self.build_output_filename("semua_sheet_valid"),
                initialdir=os.path.dirname(self.excel_path)
            )
            if save_path:
                save_workbook(
                    all_sheets,
                    save_path,
                    log_rows=log_rows,
                    mismatch_details=mismatch_details
                )
                self.set_last_saved_path(save_path)
                self.status.config(
                    text=(
                        f"{processed_sheets} sheet valid selesai disinkronkan "
                        f"({total_matches} file cocok).\n"
                        f"File disimpan di:\n{save_path}"
                    ),
                    fg="green"
                )
            else:
                self.status.config(text="Proses dibatalkan, file tidak disimpan.", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Terjadi kesalahan:\n{str(e)}")
            self.status.config(text="Sinkronisasi semua sheet gagal.", fg="red")

if __name__ == "__main__":
    root = tk.Tk()
    app = SyncApp(root)
    root.mainloop()

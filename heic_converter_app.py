import json
import os
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image

from audit_image_formats import DEFAULT_ROOTS, detect_actual_format


SUPPORTED_HEIC_EXTENSIONS = {".heic", ".heif", ".jpg", ".jpeg"}


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def ensure_heic_support():
    try:
        from pillow_heif import register_heif_opener
    except ImportError as exc:
        raise RuntimeError(
            "Dependensi `pillow-heif` belum terpasang.\n"
            "Install dulu dengan perintah:\n"
            "pip install pillow-heif"
        ) from exc

    register_heif_opener()


def find_heic_candidates(roots):
    candidates = []

    for root in roots:
        root_path = Path(root)
        for file_path in sorted(root_path.rglob("*")):
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() not in SUPPORTED_HEIC_EXTENSIONS:
                continue

            actual_format, note = detect_actual_format(file_path)
            if actual_format != "heic":
                continue

            relative_path = file_path.relative_to(root_path)
            candidates.append(
                {
                    "source_root": root_path,
                    "source_path": file_path,
                    "relative_path": relative_path,
                    "source_extension": file_path.suffix.lower(),
                    "note": note,
                }
            )

    return candidates


def build_output_path(output_root, candidate):
    relative_parent = candidate["relative_path"].parent
    source_stem = candidate["source_path"].stem
    target_dir = Path(output_root) / relative_parent
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / f"{source_stem}.jpg"
    if target_path.exists():
        target_path = target_dir / f"{source_stem}__from_heic.jpg"

    return target_path


def convert_candidates(candidates, output_root, quality=95):
    ensure_heic_support()

    results = []
    for candidate in candidates:
        source_path = candidate["source_path"]
        output_path = build_output_path(output_root, candidate)

        with Image.open(source_path) as image:
            rgb_image = image.convert("RGB")
            rgb_image.save(output_path, format="JPEG", quality=quality)

        results.append(
            {
                "source_path": str(source_path),
                "output_path": str(output_path),
            }
        )

    return results


class HeicConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Converter HEIC ke JPG")
        self.root.geometry("760x560")

        self.source_roots = []
        self.candidates = []
        self.output_dir = None
        self.automation = self.load_automation_settings()

        self.title_label = tk.Label(
            root,
            text="Scan dan convert file HEIC atau file .jpg yang ternyata HEIC"
        )
        self.title_label.pack(pady=8)

        self.source_actions = tk.Frame(root)
        self.source_actions.pack(pady=5)

        self.btn_use_default = tk.Button(
            self.source_actions,
            text="Gunakan Folder Default",
            command=self.use_default_roots
        )
        self.btn_use_default.pack(side="left", padx=5)

        self.btn_add_folder = tk.Button(
            self.source_actions,
            text="Tambah Folder",
            command=self.add_folder
        )
        self.btn_add_folder.pack(side="left", padx=5)

        self.btn_reset_folders = tk.Button(
            self.source_actions,
            text="Reset Folder",
            command=self.reset_folders
        )
        self.btn_reset_folders.pack(side="left", padx=5)

        self.source_label = tk.Label(root, text="Folder sumber:")
        self.source_label.pack(anchor="w", padx=15, pady=(10, 0))

        self.source_list = tk.Listbox(root, height=6, width=100)
        self.source_list.pack(fill="x", padx=15, pady=5)

        self.output_frame = tk.Frame(root)
        self.output_frame.pack(fill="x", padx=15, pady=5)

        self.btn_output = tk.Button(
            self.output_frame,
            text="Pilih Folder Output",
            command=self.choose_output_dir
        )
        self.btn_output.pack(side="left")

        self.output_label = tk.Label(
            self.output_frame,
            text="Folder output belum dipilih",
            anchor="w"
        )
        self.output_label.pack(side="left", padx=10)

        self.action_frame = tk.Frame(root)
        self.action_frame.pack(pady=15)

        self.btn_scan = tk.Button(
            self.action_frame,
            text="Scan Kandidat HEIC",
            command=self.scan_candidates
        )
        self.btn_scan.pack(side="left", padx=5)

        self.btn_convert = tk.Button(
            self.action_frame,
            text="Convert ke JPG",
            command=self.convert_all,
            state=tk.DISABLED
        )
        self.btn_convert.pack(side="left", padx=5)

        self.status = tk.Label(root, text="", fg="green", justify="left")
        self.status.pack(fill="x", padx=15, pady=5)

        self.log_text = tk.Text(root, height=18, wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=15, pady=10)
        self.log("Aplikasi siap. Pilih folder sumber dan folder output.")

        if self.automation:
            self.root.after(300, self.run_automation_workflow)

    def log(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def load_automation_settings(self):
        if not env_flag("HEIC_CONVERTER_AUTOMATION"):
            return None

        roots_raw = os.getenv("HEIC_CONVERTER_AUTOMATION_ROOTS", "").strip()
        source_roots = []
        if roots_raw:
            source_roots = [
                Path(item.strip())
                for item in roots_raw.split(";")
                if item.strip()
            ]

        return {
            "source_roots": source_roots,
            "use_default_folders": env_flag(
                "HEIC_CONVERTER_AUTOMATION_USE_DEFAULT_FOLDERS", True
            ),
            "output_dir": os.getenv("HEIC_CONVERTER_AUTOMATION_OUTPUT", "").strip() or None,
            "report_path": os.getenv("HEIC_CONVERTER_AUTOMATION_REPORT", "").strip() or None,
            "close_on_finish": env_flag("HEIC_CONVERTER_AUTOMATION_CLOSE", True),
        }

    def write_automation_report(self, status, message, **extra):
        if not self.automation or not self.automation.get("report_path"):
            return

        report_path = Path(self.automation["report_path"])
        if report_path.parent:
            report_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "status": status,
            "message": message,
            "source_roots": [str(path) for path in self.source_roots],
            "output_dir": str(self.output_dir) if self.output_dir else None,
            "candidate_count": len(self.candidates),
            **extra,
        }
        report_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def set_source_roots(self, roots):
        self.source_roots = list(roots)
        self.refresh_source_list()
        self.update_convert_state()

    def set_output_dir(self, output_dir):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_label.config(text=str(self.output_dir))
        self.update_convert_state()

    def scan_candidates_automation(self):
        self.candidates = find_heic_candidates(self.source_roots)
        total = len(self.candidates)
        self.status.config(
            text=f"Ditemukan {total} file kandidat HEIC untuk dikonversi.",
            fg="green" if total else "red"
        )
        self.log(f"Scan selesai. Kandidat ditemukan: {total}")
        self.update_convert_state()
        return total

    def convert_all_automation(self):
        if not self.candidates:
            raise ValueError("Tidak ada kandidat HEIC untuk dikonversi.")
        if not self.output_dir:
            raise ValueError("Folder output belum dipilih.")

        results = convert_candidates(self.candidates, self.output_dir)
        self.status.config(
            text=f"Convert selesai. Total file JPG dibuat: {len(results)}",
            fg="green"
        )
        self.log(f"Convert selesai. File dibuat: {len(results)}")
        return results

    def run_automation_workflow(self):
        try:
            roots = []
            if self.automation["use_default_folders"]:
                missing_roots = [str(path) for path in DEFAULT_ROOTS if not Path(path).is_dir()]
                if missing_roots:
                    raise FileNotFoundError(
                        "Folder default tidak ditemukan:\n" + "\n".join(missing_roots)
                    )
                roots = list(DEFAULT_ROOTS)
                self.log(f"Memuat {len(roots)} folder default.")
            elif self.automation["source_roots"]:
                roots = self.automation["source_roots"]

            if not roots:
                raise ValueError("Folder sumber otomasi belum diisi.")

            invalid_roots = [str(path) for path in roots if not Path(path).is_dir()]
            if invalid_roots:
                raise FileNotFoundError(
                    "Folder sumber tidak ditemukan:\n" + "\n".join(invalid_roots)
                )

            output_dir = self.automation["output_dir"]
            if not output_dir:
                raise ValueError("HEIC_CONVERTER_AUTOMATION_OUTPUT wajib diisi.")

            self.set_source_roots(roots)
            self.set_output_dir(output_dir)
            total_candidates = self.scan_candidates_automation()
            results = self.convert_all_automation()
            self.write_automation_report(
                "success",
                "Convert otomatis berhasil.",
                total_candidates=total_candidates,
                converted_count=len(results),
                sample_outputs=[item["output_path"] for item in results[:10]],
            )
        except Exception as exc:
            self.status.config(text="Convert otomatis gagal.", fg="red")
            self.log(traceback.format_exc())
            self.write_automation_report("error", str(exc))
        finally:
            if self.automation["close_on_finish"]:
                self.root.after(300, self.root.destroy)

    def refresh_source_list(self):
        self.source_list.delete(0, "end")
        for path in self.source_roots:
            self.source_list.insert("end", str(path))

    def use_default_roots(self):
        missing_roots = [str(path) for path in DEFAULT_ROOTS if not Path(path).is_dir()]
        if missing_roots:
            if not self.automation:
                messagebox.showerror(
                    "Error",
                    "Folder default tidak ditemukan:\n" + "\n".join(missing_roots)
                )
            return

        self.set_source_roots(DEFAULT_ROOTS)
        self.log(f"Memuat {len(self.source_roots)} folder default.")

    def add_folder(self):
        path = filedialog.askdirectory()
        if not path:
            return

        path_obj = Path(path)
        if path_obj not in self.source_roots:
            self.source_roots.append(path_obj)
            self.refresh_source_list()
            self.log(f"Menambahkan folder sumber: {path_obj}")
        self.update_convert_state()

    def reset_folders(self):
        self.source_roots = []
        self.candidates = []
        self.refresh_source_list()
        self.update_convert_state()
        self.status.config(text="Folder sumber direset.", fg="red")
        self.log("Folder sumber direset.")

    def choose_output_dir(self):
        path = filedialog.askdirectory()
        if not path:
            return

        self.set_output_dir(path)
        self.log(f"Folder output: {self.output_dir}")

    def update_convert_state(self):
        if self.source_roots and self.output_dir and self.candidates:
            self.btn_convert.config(state=tk.NORMAL)
        else:
            self.btn_convert.config(state=tk.DISABLED)

    def scan_candidates(self):
        if not self.source_roots:
            messagebox.showwarning("Peringatan", "Pilih minimal satu folder sumber.")
            return

        try:
            self.candidates = find_heic_candidates(self.source_roots)
            total = len(self.candidates)
            self.status.config(
                text=f"Ditemukan {total} file kandidat HEIC untuk dikonversi.",
                fg="green" if total else "red"
            )
            self.log(f"Scan selesai. Kandidat ditemukan: {total}")

            preview_limit = 20
            for candidate in self.candidates[:preview_limit]:
                self.log(
                    f"- {candidate['source_path'].name} "
                    f"({candidate['source_extension']} -> jpg)"
                )

            if total > preview_limit:
                self.log(f"... dan {total - preview_limit} file lainnya.")
        except Exception as exc:
            messagebox.showerror("Error", f"Terjadi kesalahan saat scan:\n{exc}")
            self.status.config(text="Scan gagal.", fg="red")
            self.log(traceback.format_exc())
        finally:
            self.update_convert_state()

    def convert_all(self):
        if not self.candidates:
            messagebox.showwarning("Peringatan", "Belum ada kandidat hasil scan.")
            return

        if not self.output_dir:
            messagebox.showwarning("Peringatan", "Pilih folder output terlebih dahulu.")
            return

        confirm = messagebox.askyesno(
            "Konfirmasi Convert",
            (
                f"Total file yang akan dikonversi: {len(self.candidates)}\n"
                f"Folder output:\n{self.output_dir}\n\n"
                "Lanjutkan convert?"
            ),
        )
        if not confirm:
            self.status.config(text="Convert dibatalkan.", fg="red")
            return

        try:
            results = convert_candidates(self.candidates, self.output_dir)
            self.status.config(
                text=f"Convert selesai. Total file JPG dibuat: {len(results)}",
                fg="green"
            )
            self.log(f"Convert selesai. File dibuat: {len(results)}")
            for item in results[:20]:
                self.log(
                    f"- {Path(item['source_path']).name} -> "
                    f"{Path(item['output_path']).name}"
                )
            if len(results) > 20:
                self.log(f"... dan {len(results) - 20} file lainnya.")
            messagebox.showinfo(
                "Selesai",
                (
                    f"Convert selesai.\n"
                    f"Total file JPG dibuat: {len(results)}\n"
                    f"Folder output:\n{self.output_dir}"
                ),
            )
        except Exception as exc:
            messagebox.showerror("Error", f"Convert gagal:\n{exc}")
            self.status.config(text="Convert gagal.", fg="red")
            self.log(traceback.format_exc())


if __name__ == "__main__":
    root = tk.Tk()
    app = HeicConverterApp(root)
    root.mainloop()

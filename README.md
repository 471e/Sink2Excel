# Sinkronisasi File Gambar Dengan Excel

Project ini dipakai untuk mencocokkan nama file gambar di Excel dengan file gambar lokal, lalu mengganti isi kolom foto menjadi path lokal yang lengkap.

Saat ini tersedia 2 cara pakai:

- `importos.py` untuk mode GUI
- `importpan.py` untuk mode CLI/terminal
- `heic_converter_app.py` untuk convert `HEIC` ke `JPG`

Keduanya memakai logika inti yang sama dari `sync_core.py`.

## Fitur

- Mendukung 3 kolom foto wajib:
  - `Foto KTP`
  - `Foto Rumah`
  - `Foto Meter Listrik`
- Mendukung 1 kolom foto opsional:
  - `Foto Lainnya`
- Kolom `Foto Lainnya` hanya diproses jika kolom itu ada di sheet dan foldernya diisi manual
- Bisa memproses `sheet terpilih` atau `semua sheet valid`
- Pencocokan nama file bersifat `case-insensitive`
- Menambahkan audit sheet ke output:
  - `Log Sinkronisasi`
  - `Detail Tidak Cocok` jika ada mismatch
- Workbook output otomatis diberi formatting ringan:
  - header tebal
  - autofilter
  - freeze pane
  - highlight untuk mismatch

## Struktur File

- `importos.py`: aplikasi GUI berbasis Tkinter
- `importpan.py`: script CLI
- `sync_core.py`: logika inti sinkronisasi
- `audit_image_formats.py`: audit format asli file gambar
- `fix_mislabeled_heic.py`: rename aman untuk file `.jpg` yang ternyata `HEIC`
- `heic_converter_app.py`: aplikasi converter `HEIC` ke `JPG`

## Dependensi

Install dependensi dengan:

```bash
pip install -r requirements.txt
```

Isi `requirements.txt` saat ini:

```text
pandas==2.3.3
openpyxl==3.1.5
pillow==12.1.0
pillow-heif==1.4.0
```

Untuk kebutuhan build `.exe`:

```bash
pip install -r requirements-dev.txt
```

## Folder Default

Script sudah menyimpan path default berikut:

```text
Foto KTP            C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto KTP (File responses)
Foto Rumah          C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto Rumah (File responses)
Foto Meter Listrik  C:\Users\alfa-raffa\Downloads\(RC) Calon Pelanggan Kegiatan Prioritas Air Minum 2026\Foto Meter Listrik (File responses)
```

Catatan:

- `Foto Lainnya` tidak memakai folder default
- Jika ingin memproses `Foto Lainnya`, pilih foldernya manual di GUI atau isi argumen CLI `--foto-lainnya`

## Cara Pakai GUI

Jalankan:

```bash
python importos.py
```

Alur pakai:

1. Klik `Browse Excel`
2. Pilih sheet jika ingin proses satu sheet
3. Klik `Isi Folder Default` atau pilih folder manual
   - untuk `Foto Lainnya`, pilih folder manual jika kolom itu ada di sheet
4. Pilih salah satu aksi:
   - `Sinkronisasi Sheet Terpilih`
   - `Sinkronisasi Semua Sheet Valid`
5. Cek preview
6. Simpan file output
7. Jika perlu, klik `Buka Folder Hasil`

### Mode otomasi GUI sinkronisasi

Mode ini dipakai untuk uji executable secara deterministik tanpa klik manual.

Contoh:

```powershell
$env:SYNC_APP_AUTOMATION = "1"
$env:SYNC_APP_AUTOMATION_EXCEL = "C:\path\data.xlsx"
$env:SYNC_APP_AUTOMATION_MODE = "all"
$env:SYNC_APP_AUTOMATION_USE_DEFAULT_FOLDERS = "1"
$env:SYNC_APP_AUTOMATION_OUTPUT = "C:\path\hasil.xlsx"
$env:SYNC_APP_AUTOMATION_REPORT = "C:\path\hasil.json"
$env:SYNC_APP_AUTOMATION_CLOSE = "1"
python importos.py
```

Environment variable yang didukung:

- `SYNC_APP_AUTOMATION`
  - aktifkan mode otomasi
- `SYNC_APP_AUTOMATION_EXCEL`
  - path file Excel sumber
- `SYNC_APP_AUTOMATION_MODE`
  - `selected` atau `all`
- `SYNC_APP_AUTOMATION_USE_DEFAULT_FOLDERS`
  - `1` untuk memakai folder default
- `SYNC_APP_AUTOMATION_OUTPUT`
  - path workbook output
- `SYNC_APP_AUTOMATION_REPORT`
  - path file JSON ringkasan hasil
- `SYNC_APP_AUTOMATION_CLOSE`
  - `1` agar window menutup otomatis setelah selesai

## Cara Pakai CLI

### Proses semua sheet valid dengan folder default

```bash
python importpan.py "Form RC Calon Pelanggan AM 2026 Prov. Malut (1).xlsx" --all-sheets --use-default-folders
```

### Proses satu sheet tertentu

```bash
python importpan.py "Form RC Calon Pelanggan AM 2026 Prov. Malut (1).xlsx" --sheet Somahode --use-default-folders
```

### Proses dengan folder manual

```bash
python importpan.py "data.xlsx" --all-sheets --foto-ktp "C:\path\ktp" --foto-rumah "C:\path\rumah" --foto-meter-listrik "C:\path\meter"
```

### Proses dengan kolom opsional `Foto Lainnya`

```bash
python importpan.py "data.xlsx" --all-sheets --foto-ktp "C:\path\ktp" --foto-rumah "C:\path\rumah" --foto-meter-listrik "C:\path\meter" --foto-lainnya "C:\path\lainnya"
```

### Simpan ke nama file tertentu

```bash
python importpan.py "data.xlsx" --all-sheets --use-default-folders --output "hasil_sinkron.xlsx"
```

## Cara Pakai Converter

Jalankan:

```bash
python heic_converter_app.py
```

Alur pakai:

1. Klik `Gunakan Folder Default` atau `Tambah Folder`
2. Pilih `Folder Output`
3. Klik `Scan Kandidat HEIC`
4. Cek jumlah kandidat
5. Klik `Convert ke JPG`

Catatan:

- Converter memproses file `.heic`, `.heif`, dan file `.jpg/.jpeg` yang ternyata isi aslinya `HEIC`
- File asli tidak diubah
- Hasil `JPG` ditulis ke folder output terpisah
- Struktur subfolder dipertahankan

### Mode otomasi converter

Mode ini dipakai untuk uji converter pada source Python maupun `.exe`.

Contoh:

```powershell
$env:HEIC_CONVERTER_AUTOMATION = "1"
$env:HEIC_CONVERTER_AUTOMATION_USE_DEFAULT_FOLDERS = "1"
$env:HEIC_CONVERTER_AUTOMATION_OUTPUT = "C:\path\output_converter"
$env:HEIC_CONVERTER_AUTOMATION_REPORT = "C:\path\output_converter\report.json"
$env:HEIC_CONVERTER_AUTOMATION_CLOSE = "1"
python heic_converter_app.py
```

Environment variable yang didukung:

- `HEIC_CONVERTER_AUTOMATION`
  - aktifkan mode otomasi
- `HEIC_CONVERTER_AUTOMATION_USE_DEFAULT_FOLDERS`
  - `1` untuk memakai 3 folder default
- `HEIC_CONVERTER_AUTOMATION_ROOTS`
  - daftar folder sumber dipisahkan `;`
- `HEIC_CONVERTER_AUTOMATION_OUTPUT`
  - folder output hasil JPG
- `HEIC_CONVERTER_AUTOMATION_REPORT`
  - path file JSON ringkasan hasil convert
- `HEIC_CONVERTER_AUTOMATION_CLOSE`
  - `1` agar window menutup otomatis setelah selesai

## Build EXE

File build tambahan:

- `requirements-dev.txt`
- `build_apps.ps1`

Install dependency build:

```bash
pip install -r requirements-dev.txt
```

Build executable:

```powershell
powershell -ExecutionPolicy Bypass -File .\build_apps.ps1
```

Output hasil build ada di folder:

```text
dist_apps\
```

Target executable:

- `dist_apps\importos.exe`
- `dist_apps\heic_converter_app.exe`

Nama file yang dipakai di paket rilis user:

- `Sinkronisasi-Excel-Gambar.exe`
- `Converter-HEIC-ke-JPG.exe`

Nama paket rilis saat ini:

- `Sinkronisasi-Excel-Tools-v1.0.1`

## Smoke Test Rilis

Untuk menguji paket rilis sekali jalan:

```powershell
powershell -ExecutionPolicy Bypass -File .\smoke_test_release.ps1
```

Script ini akan:

- menjalankan `Sinkronisasi-Excel-Gambar.exe` dalam mode otomasi
- menjalankan `Converter-HEIC-ke-JPG.exe` dalam mode otomasi
- menulis output ke folder `smoke_test_outputs`
- memverifikasi report JSON dari kedua aplikasi

File terkait:

- `smoke_test_release.ps1`
- `smoke_test_outputs\sinkronisasi_release_all.xlsx`
- `smoke_test_outputs\sinkronisasi_release_all.json`
- `smoke_test_outputs\converter_release\report_release.json`

## Parameter CLI

- `excel_path`
  - file Excel sumber
- `--sheet`
  - proses satu sheet tertentu
- `--all-sheets`
  - proses semua sheet yang punya kolom foto wajib
- `--foto-ktp`
  - folder untuk `Foto KTP`
- `--foto-rumah`
  - folder untuk `Foto Rumah`
- `--foto-meter-listrik`
  - folder untuk `Foto Meter Listrik`
- `--foto-lainnya`
  - folder untuk `Foto Lainnya` jika kolom itu ada di sheet
- `--use-default-folders`
  - pakai path default yang sudah tertanam di script
- `--output`
  - nama/path file output

## Output Excel

File hasil akan tetap menyimpan semua sheet asli workbook.

Sheet audit tambahan:

- `Log Sinkronisasi`
  - ringkasan jumlah data terisi, cocok, dan tidak cocok per sheet
- `Detail Tidak Cocok`
  - hanya muncul jika ada mismatch
  - berisi:
    - `Sheet`
    - `Baris Excel`
    - `Nama Lengkap`
    - `Kolom Foto`
    - `Nama File Dicari`

## Audit Dan Perbaikan Format Gambar

Audit format gambar:

```bash
python audit_image_formats.py --output laporan_format_gambar.csv
```

Perbaiki file `.jpg/.jpeg` yang ternyata `HEIC`:

```bash
python fix_mislabeled_heic.py --output rencana_perbaikan_heic.csv
```

Terapkan rename ke file asli:

```bash
python fix_mislabeled_heic.py --apply --output hasil_perbaikan_heic.csv
```

## Catatan

- Jika workbook tidak punya kolom wajib `Foto KTP`, `Foto Rumah`, dan `Foto Meter Listrik`, sheet tersebut tidak diproses.
- Jika sheet memiliki kolom `Foto Lainnya` dan foldernya tidak diisi, kolom itu dibiarkan apa adanya dan tidak ikut disinkronkan.
- Jika file gambar tidak ditemukan, nilai kolom akan diisi `None`.
- Nama file output otomatis dibuat lebih rapi dan memakai timestamp jika nama output tidak ditentukan manual.
- Formatting workbook hasil bisa berubah sedikit dibanding file Excel asli karena proses simpan ulang dilakukan lewat `pandas` dan `openpyxl`.

## Contoh Hasil Validasi

Pada data uji saat ini:

- total sheet valid: `8`
- total file cocok: `1641`
- total mismatch: `0`
- total kandidat converter HEIC di 3 folder default: `91`
- total file salah ekstensi `.jpg -> heic`: `18`
- build `.exe` berhasil untuk:
  - `importos.exe`
  - `heic_converter_app.exe`
- smoke test paket rilis berhasil untuk:
  - `Sinkronisasi-Excel-Gambar.exe`
  - `Converter-HEIC-ke-JPG.exe`

## Pengembangan Lanjut

Ide lanjutan yang bisa ditambahkan:

- `README` dengan screenshot GUI
- tombol `Buka File Hasil`
- icon aplikasi `.exe`

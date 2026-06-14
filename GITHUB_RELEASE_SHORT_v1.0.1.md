# Sink2Excel v1.0.1

Rilis ini menghadirkan paket executable Windows untuk sinkronisasi file gambar ke Excel dan konversi HEIC ke JPG, lengkap dengan smoke test otomatis untuk validasi rilis.

## Yang Termasuk

- `Sinkronisasi-Excel-Gambar.exe`
- `Converter-HEIC-ke-JPG.exe`
- `PANDUAN-EXE.txt`
- `README.md`
- `Sinkronisasi-Excel-Tools-v1.0.1.zip`

## Perubahan Utama

- Menambahkan mode otomasi untuk aplikasi sinkronisasi GUI.
- Menambahkan mode otomasi untuk converter HEIC ke JPG.
- Menambahkan smoke test rilis untuk dua executable.
- Memperkuat alur smoke test agar lebih andal pada aplikasi GUI one-file.
- Menyiapkan pipeline build, package, dan smoke test untuk rilis berikutnya.

## Hasil Validasi

- Sinkronisasi: `success`
- Sheet valid: `8`
- Total cocok: `1641`
- Mismatch: `0`
- Converter: `success`
- Kandidat HEIC: `91`
- Berhasil dikonversi: `91`

## Catatan

- Tag rilis tetap `v1.0.1`
- Repository: `https://github.com/471e/Sink2Excel`

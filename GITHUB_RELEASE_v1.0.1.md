# Sink2Excel v1.0.1

Rilis ini menyiapkan paket executable Windows untuk sinkronisasi file gambar ke Excel dan konversi file HEIC ke JPG, lengkap dengan jalur smoke test otomatis untuk validasi rilis.

## Isi Rilis

- `Sinkronisasi-Excel-Gambar.exe`
- `Converter-HEIC-ke-JPG.exe`
- `PANDUAN-EXE.txt`
- `README.md`
- paket zip `Sinkronisasi-Excel-Tools-v1.0.1.zip`

## Highlight

- Menambahkan mode otomasi untuk aplikasi sinkronisasi Excel berbasis GUI.
- Menambahkan mode otomasi untuk converter HEIC ke JPG.
- Menyediakan script `smoke_test_release.ps1` untuk menguji dua executable secara end-to-end.
- Memperbaiki alur smoke test agar menunggu report JSON dan lebih andal untuk aplikasi GUI one-file.
- Menstabilkan packaging rilis `v1.0.1` untuk distribusi Windows.

## Hasil Validasi

Smoke test rilis berhasil dijalankan terhadap paket `v1.0.1` dengan hasil:

- Sinkronisasi Excel: `success`
- Sheet valid diproses: `8`
- Total file cocok: `1641`
- Total mismatch: `0`
- Converter HEIC: `success`
- Total kandidat HEIC: `91`
- Total file terkonversi: `91`
- Total file JPG aktual: `91`

## Catatan

- Tag rilis: `v1.0.1`
- Repo utama: `https://github.com/471e/Sink2Excel`
- Smoke test menghasilkan `smoke_test_summary.json` sebagai ringkasan validasi teknis.

## Saran Pemakaian

- Unduh paket zip `Sinkronisasi-Excel-Tools-v1.0.1.zip`.
- Ekstrak paket ke folder lokal yang memiliki hak tulis.
- Jalankan `Sinkronisasi-Excel-Gambar.exe` untuk sinkronisasi workbook.
- Jalankan `Converter-HEIC-ke-JPG.exe` bila perlu mengonversi file HEIC atau JPG salah ekstensi.

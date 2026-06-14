# GitHub Release Publish Template v1.0.2

## Title

Sink2Excel v1.0.2

## Tag

v1.0.2

## Description

Rilis ini menambahkan dukungan kolom opsional `Foto Lainnya` tanpa mengubah kompatibilitas tiga kolom foto utama yang sudah ada.

### Perubahan Utama

- Menambahkan kolom opsional `Foto Lainnya`.
- `Foto Lainnya` hanya diproses jika kolomnya ada di sheet dan foldernya diisi manual.
- Tiga kolom utama tetap wajib: `Foto KTP`, `Foto Rumah`, dan `Foto Meter Listrik`.
- Pipeline packaging dipisahkan ke konfigurasi versi bersama untuk memudahkan rilis berikutnya.

### Catatan

- Rilis publik sebelumnya tetap `v1.0.1`.
- Rilis `v1.0.2` dimaksudkan untuk membawa dukungan `Foto Lainnya` ke paket executable berikutnya.
- Lengkapi bagian hasil validasi setelah build dan smoke test `v1.0.2` selesai dijalankan.

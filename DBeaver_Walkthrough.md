# DBeaver — Panduan Koneksi ke Database BukuRumah

Langkah-langkah untuk menghubungkan DBeaver ke database PostgreSQL yang berjalan di dalam Docker container.

## Prasyarat

1. Docker Desktop sudah berjalan
2. Container `rumah_buku_v2` sudah running (`docker compose up -d`)
3. DBeaver sudah terinstal

## Langkah-langkah

### 1. Pastikan Container Running

```bash
cd rumah_buku_v2
docker compose up -d
```

Verifikasi kedua container aktif:

```bash
docker compose ps
```

Harus terlihat `rumah_buku_odoo` dan `odoo-postgres` keduanya **Up**.

### 2. Buka DBeaver → New Connection

1. Buka DBeaver
2. Klik **Database** → **New Database Connection**
3. Pilih **PostgreSQL** → **Next**

### 3. Isi Connection Settings

| Field       | Value             |
|-------------|-------------------|
| **Host**    | `localhost`       |
| **Port**    | `5432`            |
| **Database**| `odoo_development`|
| **Username**| `odoo`            |
| **Password**| `odoo`            |

> **Note:** Port 5432 sudah di-expose di `docker-compose.yml`:
> ```yaml
> ports:
>   - "5432:5432"
> ```

### 4. Test Connection

Klik **Test Connection** di pojok kiri bawah dialog. Jika berhasil, akan muncul ✅ *Connected*.

### 5. Finish & Connect

Klik **Finish**. DBeaver akan menampilkan database `odoo_development` di panel Navigator.

### 6. Navigasi ke Tabel BukuRumah

```
odoo_development
└── public
    └── Tables
        ├── rumah_buku_book
        ├── rumah_buku_transaction
        ├── rumah_buku_payment
        ├── rumah_buku_fine
        ├── rumah_buku_notification
        └── rumah_buku_membership
```

### 7. Contoh Query

```sql
-- Lihat semua buku
SELECT id, name, author, category, status, stock, sell_price, rent_price_per_day
FROM rumah_buku_book
ORDER BY create_date DESC;

-- Lihat transaksi aktif
SELECT t.id, b.name AS book, u.login AS user_email, t.transaction_type, t.status, t.total_amount
FROM rumah_buku_transaction t
JOIN rumah_buku_book b ON t.book_id = b.id
JOIN res_users u ON t.user_id = u.id
WHERE t.status IN ('borrowed', 'ready_for_pickup')
ORDER BY t.create_date DESC;

-- Lihat denda yang belum dibayar
SELECT f.id, u.login, f.amount, f.reason, f.status
FROM rumah_buku_fine f
JOIN res_users u ON f.user_id = u.id
WHERE f.status = 'unpaid';

-- Lihat keanggotaan aktif
SELECT m.id, u.login, m.plan, m.monthly_fee, m.status, m.start_date, m.expiry_date
FROM rumah_buku_membership m
JOIN res_users u ON m.user_id = u.id
WHERE m.status = 'active';
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Pastikan container PostgreSQL running: `docker compose ps` |
| Port already in use | Ada PostgreSQL lain di port 5432. Stop dulu atau ubah port di `docker-compose.yml` |
| Access denied | Cek username/password di `.env` file |
| Database not found | Pastikan Odoo sudah pernah diakses dan database `odoo_development` sudah terbuat |

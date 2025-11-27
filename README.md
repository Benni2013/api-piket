# API Piket - Face Recognition & Attendance System

API untuk sistem absensi piket menggunakan face recognition dengan FaceNet, terintegrasi dengan database SILAB dari Laravel.

## 📋 Deskripsi

API Piket adalah REST API yang menyediakan layanan:
1. **Face Recognition** - Pengenalan wajah menggunakan FaceNet (512-dimensional embeddings)
2. **Face Vector Management** - Insert & Update vektor wajah dari kamera atau upload foto
3. **Attendance System** - Absensi piket dengan verification wajah real-time

## 🎯 Fitur Utama

### 6 Endpoint Layanan:

1. **Health Check** - Cek status API dan database
2. **Insert Face Vectors (Camera)** - Tambah vektor wajah dengan 20 foto dari streaming kamera
3. **Update Face Vectors** - Update vektor wajah dengan 20 foto baru
4. **Mulai Piket** - Absensi mulai piket dengan face recognition (1 foto)
5. **Akhiri Piket** - Absensi akhir piket dengan verifikasi wajah + input kegiatan (1 foto)
6. **Insert Face Vector (Photo)** - Tambah 1 vektor wajah dari upload foto

## 🛠️ Teknologi

- **Framework**: Flask 3.0+
- **Database**: MySQL 8.0+ (Database SILAB)
- **Face Recognition**: FaceNet (keras-facenet 0.3.2)
- **Computer Vision**: OpenCV 4.9+
- **Deep Learning**: TensorFlow 2.15+
- **ORM**: Flask-SQLAlchemy 3.1+

## 📦 Instalasi

### 1. Clone Repository

```bash
git clone <repository-url>
cd api-piket
```

### 2. Setup Python Environment

```bash
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Database

#### 3.1 Import Database SILAB

```bash
# Buat database silab
mysql -u root -p -e "CREATE DATABASE silab;"

# Import struktur database
mysql -u root -p silab < silab.sql
```

#### 3.2 Buat Tabel vektor_wajah

```sql
-- Login ke MySQL
mysql -u root -p silab

-- Buat tabel vektor_wajah
CREATE TABLE vektor_wajah (
    id_vektor_wajah INT PRIMARY KEY AUTO_INCREMENT,
    user_id CHAR(36) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    vektor JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 4. Konfigurasi Environment

```bash
# Copy .env.example ke .env
copy .env.example .env

# Edit file .env
notepad .env
```

Isi file `.env`:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=silab

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Face Recognition
SIMILARITY_THRESHOLD=0.7
MAX_IMAGES_PER_PERSON=20

# Upload Configuration
UPLOAD_FOLDER=data/wajah
```

### 5. Jalankan Aplikasi

```bash
# Development mode
python app.py

# Production mode (gunakan gunicorn)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

API akan berjalan di: **`http://localhost:5000`**

## 📚 Dokumentasi API

### Endpoint 1: Health Check

**GET** `/health`

Mengecek status API dan koneksi database.

**Response:**
```json
{
  "status": "ok",
  "message": "API Piket is running",
  "database": "connected",
  "timestamp": "2025-11-27T10:00:00",
  "version": "3.0"
}
```

---

### Endpoint 2: Insert Face Vectors (Camera)

**POST** `/api/face/insert`

Insert vektor wajah user dengan multiple images dari streaming kamera (max 20 foto).

**Request Body:**
```json
{
  "user_id": "uuid-string",
  "images": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "... (max 20 images)"
  ]
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Successfully saved 20 face vectors for John Doe",
  "data": {
    "user_id": "uuid-string",
    "name": "John Doe",
    "total_images_processed": 20,
    "embeddings_saved": 20,
    "errors": null
  }
}
```

**Response Error (400/404/409):**
```json
{
  "success": false,
  "message": "Error message",
  "errors": ["Image 1: No face detected", "..."]
}
```

**Catatan:**
- User harus sudah terdaftar di database SILAB (tabel `users`)
- Setiap user hanya bisa insert sekali, gunakan endpoint update untuk menambah/ubah vektor
- Minimal 1 foto, maksimal 20 foto
- Sistem akan auto-detect face di setiap foto
- Foto yang tidak terdeteksi wajahnya akan di-skip

---

### Endpoint 3: Update Face Vectors

**PUT** `/api/face/update/<user_id>`

Update vektor wajah user dengan multiple images baru (max 20 foto). Vektor lama akan dihapus dan diganti dengan yang baru.

**URL Parameter:**
- `user_id` (string, required): UUID dari user

**Request Body:**
```json
{
  "images": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "... (max 20 images)"
  ]
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Successfully updated face vectors for John Doe",
  "data": {
    "user_id": "uuid-string",
    "name": "John Doe",
    "old_vectors_count": 20,
    "new_vectors_count": 20,
    "total_images_processed": 20,
    "errors": null
  }
}
```

---

### Endpoint 4: Mulai Piket

**POST** `/api/piket/mulai`

Mulai piket dengan face recognition real-time (1 foto).

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Piket dimulai untuk John Doe",
  "data": {
    "id": "uuid-absensi",
    "user_id": "uuid-user",
    "name": "John Doe",
    "tanggal": "2025-11-27",
    "jam_masuk": "08:00:00",
    "jam_keluar": null,
    "kegiatan": "",
    "foto": "",
    "jadwal_piket": "uuid-jadwal",
    "periode_piket_id": "uuid-periode",
    "similarity": 0.95,
    "created_at": "2025-11-27T08:00:00",
    "updated_at": "2025-11-27T08:00:00"
  }
}
```

**Response Error:**
```json
{
  "success": false,
  "message": "Face not recognized. Please register first."
}
```

**Response Error (No Schedule):**
```json
{
  "success": false,
  "message": "John Doe tidak memiliki jadwal piket"
}
```

**Response Error (Already Started):**
```json
{
  "success": false,
  "message": "John Doe sudah mulai piket hari ini"
}
```

**Catatan:**
- Wajah harus sudah terdaftar (ada vektor wajah di database)
- User harus memiliki jadwal piket (`jadwal_piket` table)
- Similarity threshold default: 0.7 (bisa diubah di `.env`)
- Hanya bisa mulai piket 1x per hari per jadwal
- Memerlukan periode piket aktif (`isactive=1`)
- Field `foto` dan `kegiatan` akan diisi string kosong saat mulai piket

---

### Endpoint 5: Akhiri Piket

**POST** `/api/piket/akhiri`

Akhiri piket dengan face verification dan input kegiatan (1 foto).

**Request Body:**
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "kegiatan": "Membersihkan lab, mengecek komputer, update inventaris"
}
```

**Response Success (200):**
```json
{
  "success": true,
  "message": "Piket selesai untuk John Doe",
  "data": {
    "id": "uuid-absensi",
    "user_id": "uuid-user",
    "name": "John Doe",
    "tanggal": "2025-11-27",
    "jam_masuk": "08:00:00",
    "jam_keluar": "12:00:00",
    "durasi": "4 jam 0 menit",
    "kegiatan": "Membersihkan lab, mengecek komputer, update inventaris",
    "similarity": 0.96,
    "created_at": "2025-11-27T08:00:00",
    "updated_at": "2025-11-27T12:00:00"
  }
}
```

**Response Error:**
```json
{
  "success": false,
  "message": "John Doe belum mulai piket hari ini"
}
```

**Response Error (No Schedule):**
```json
{
  "success": false,
  "message": "John Doe tidak memiliki jadwal piket"
}
```

**Response Error (Already Ended):**
```json
{
  "success": false,
  "message": "John Doe sudah mengakhiri piket hari ini"
}
```

**Catatan:**
- Harus sudah mulai piket terlebih dahulu (ada record absensi hari ini)
- User harus memiliki jadwal piket
- Kegiatan wajib diisi
- Hanya bisa akhiri piket 1x per hari per jadwal

---

### Endpoint 6: Insert Face Vector (Photo)

**POST** `/api/face/insert-from-photo`

Buat dan tambah 1 vektor wajah dari upload foto (bukan streaming kamera).

**Request Body:**
```json
{
  "user_id": "uuid-string",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

**Response Success (201):**
```json
{
  "success": true,
  "message": "Face vector saved successfully for John Doe",
  "data": {
    "user_id": "uuid-string",
    "name": "John Doe",
    "vector_id": 123,
    "total_vectors": 5
  }
}
```

**Catatan:**
- Endpoint ini untuk menambahkan vektor satu per satu
- Cocok untuk upload foto manual, bukan streaming kamera
- Tidak ada limit jumlah vektor per user (tapi recommended max 20)
- Bisa digunakan untuk melengkapi vektor yang sudah ada

---

## 🔄 Flow Penggunaan

### Scenario 1: Registrasi Face Vector (Streaming Kamera)

```
1. User terdaftar di SILAB (tabel users)
2. Web app capture 20 foto secara otomatis
3. POST /api/face/insert dengan 20 images
4. API extract embedding dari setiap foto
5. Simpan 20 vektor wajah ke database
```

### Scenario 2: Absensi Piket

```
1. User foto diri dengan kamera (1 foto)
2. POST /api/piket/mulai dengan 1 image
3. API extract embedding dan matching dengan database
4. Jika cocok, create record absensi dengan jam_masuk
5. ...user melakukan piket...
6. User foto diri lagi (1 foto)
7. POST /api/piket/akhiri dengan 1 image + kegiatan
8. API verifikasi wajah dan update jam_keluar
```

### Scenario 3: Update Face Vector

```
1. User ingin update foto (misal: ganti kacamata, gaya rambut)
2. Web app capture 20 foto baru
3. PUT /api/face/update/<user_id> dengan 20 images
4. API hapus vektor lama dan simpan vektor baru
```

---

## 🧪 Testing dengan cURL

### 1. Health Check

```bash
curl http://localhost:5000/health
```

### 2. Insert Face Vectors

```bash
curl -X POST http://localhost:5000/api/face/insert \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "your-user-uuid",
    "images": ["data:image/jpeg;base64,...", "..."]
  }'
```

### 3. Mulai Piket

```bash
curl -X POST http://localhost:5000/api/piket/mulai \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,..."
  }'
```

### 4. Akhiri Piket

```bash
curl -X POST http://localhost:5000/api/piket/akhiri \
  -H "Content-Type: application/json" \
  -d '{
    "image": "data:image/jpeg;base64,...",
    "kegiatan": "Membersihkan lab"
  }'
```

---

## 🗂️ Struktur Database

### Tabel yang Digunakan:

#### 1. **users** (dari SILAB - Read Only)
```sql
- id (CHAR(36) PRIMARY KEY) - UUID
- name (VARCHAR(255))
- email (VARCHAR(255))
- password (VARCHAR(255))
- created_at, updated_at (TIMESTAMP)
```

#### 2. **profile** (dari SILAB - Read Only)
```sql
- id (CHAR(36) PRIMARY KEY) - UUID
- user_id (CHAR(36) FOREIGN KEY -> users.id)
- npm (VARCHAR(255))
- foto_wajah (VARCHAR(255))
- created_at, updated_at (TIMESTAMP)
```

#### 3. **vektor_wajah** (Dikelola oleh API Piket)
```sql
- id_vektor_wajah (INT PRIMARY KEY AUTO_INCREMENT)
- user_id (CHAR(36) FOREIGN KEY -> users.id)
- vektor (JSON) - 512-dimensional array
- created_at, updated_at (TIMESTAMP)
```

#### 4. **jadwal_piket** (dari SILAB - Read Only)
```sql
- id (CHAR(36) PRIMARY KEY) - UUID
- user_id (CHAR(36) FOREIGN KEY -> users.id)
- hari (VARCHAR(255))
- kepengurusan_lab_id (CHAR(36)) - Relasi ke kepengurusan_lab
- created_at, updated_at (TIMESTAMP)
```

#### 5. **periode_piket** (dari SILAB - Read Only)
```sql
- id (CHAR(36) PRIMARY KEY) - UUID
- kepengurusan_lab_id (CHAR(36)) - Relasi ke kepengurusan_lab
- nama (VARCHAR(255))
- tanggal_mulai, tanggal_selesai (DATE)
- isactive (BOOLEAN)
- created_at, updated_at (TIMESTAMP)
```

#### 6. **absensi** (Dikelola oleh API Piket)
```sql
- id (CHAR(36) PRIMARY KEY) - UUID
- tanggal (DATE)
- jam_masuk, jam_keluar (TIME)
- foto (VARCHAR(255)) - string kosong saat mulai, bisa diisi saat akhiri
- jadwal_piket (CHAR(36) FOREIGN KEY -> jadwal_piket.id)
- kegiatan (TEXT) - string kosong saat mulai, wajib diisi saat akhiri
- periode_piket_id (CHAR(36) FOREIGN KEY -> periode_piket.id)
- created_at, updated_at (TIMESTAMP)

CATATAN: Tabel absensi TIDAK memiliki kolom user_id.
User diakses melalui relasi: absensi -> jadwal_piket -> user
```

---

## ⚙️ Konfigurasi

### Environment Variables (.env)

| Variable | Default | Deskripsi |
|----------|---------|-----------|
| `DB_HOST` | localhost | Host database MySQL |
| `DB_PORT` | 3306 | Port database MySQL |
| `DB_USER` | root | Username database |
| `DB_PASSWORD` | - | Password database |
| `DB_NAME` | silab | Nama database |
| `FLASK_ENV` | development | Environment Flask (development/production) |
| `SECRET_KEY` | - | Secret key untuk Flask session |
| `SIMILARITY_THRESHOLD` | 0.7 | Threshold untuk face matching (0.0-1.0) |
| `MAX_IMAGES_PER_PERSON` | 20 | Maksimal foto per user |
| `UPLOAD_FOLDER` | data/wajah | Folder untuk simpan foto (opsional) |

---

## 🐛 Troubleshooting

### Problem 1: Database connection error

**Solusi:**
```bash
# Cek MySQL service
net start | findstr MySQL

# Test koneksi
mysql -u root -p silab -e "SELECT 1"

# Cek credentials di .env
```

### Problem 2: No face detected

**Solusi:**
- Pastikan pencahayaan cukup
- Wajah menghadap kamera (frontal)
- Jarak 30-50cm dari kamera
- Tidak ada halangan (masker, kacamata hitam, topi)

### Problem 3: Face not recognized (similarity terlalu rendah)

**Solusi:**
- Tambah lebih banyak foto saat insert (gunakan 20 foto)
- Gunakan foto dengan variasi angle/expresi
- Lower threshold di `.env`: `SIMILARITY_THRESHOLD=0.6`
- Update vektor wajah dengan foto baru yang lebih jelas

### Problem 4: Tidak ada periode piket aktif

**Solusi:**
```sql
-- Aktifkan periode piket
UPDATE periode_piket 
SET isactive = 1 
WHERE tanggal_mulai <= CURDATE() 
  AND tanggal_selesai >= CURDATE();

-- Atau buat periode baru
INSERT INTO periode_piket (id, kepengurusan_lab_id, nama, tanggal_mulai, tanggal_selesai, isactive, created_at, updated_at)
VALUES (UUID(), 'your-kepengurusan-id', 'Testing Nov 2025', '2025-11-01', '2025-11-30', 1, NOW(), NOW());
```

### Problem 5: Error "Unknown column 'absensi.user_id'"

**Penyebab:** 
Tabel `absensi` tidak memiliki kolom `user_id`. User diakses melalui relasi `jadwal_piket`.

**Solusi:**
- Pastikan API menggunakan versi terbaru (sudah fixed di v3.0)
- Restart API server setelah update
- Clear `__pycache__` folders
- Verifikasi struktur tabel: `DESCRIBE absensi;` (seharusnya tidak ada kolom `user_id`)

### Problem 6: Error "tidak memiliki jadwal piket"

**Penyebab:**
User yang recognized tidak memiliki jadwal piket di database.

**Solusi:**
```sql
-- Check jadwal user
SELECT * FROM jadwal_piket WHERE user_id = 'your-user-uuid';

-- Jika tidak ada, tambahkan jadwal
INSERT INTO jadwal_piket (id, user_id, hari, kepengurusan_lab_id, created_at, updated_at)
VALUES (UUID(), 'your-user-uuid', 'Senin', 'your-kepengurusan-id', NOW(), NOW());
```

---

## 📝 Notes

### Face Recognition Algorithm

- **Model**: FaceNet (Inception ResNet v1)
- **Embedding Size**: 512 dimensions
- **Similarity Metric**: Cosine Similarity
- **Threshold**: 0.7 (70% kecocokan)
- **Face Detection**: Haar Cascade Classifier (OpenCV)

### Best Practices

1. **Insert Face Vectors**: Gunakan 15-20 foto untuk akurasi terbaik
2. **Photo Quality**: Resolusi minimal 640x480, pencahayaan baik
3. **Face Angle**: Frontal face dengan variasi angle ringan (±15°)
4. **Update Frequency**: Update vektor wajah setiap 6 bulan atau saat perubahan signifikan (rambut, kacamata, dll)
5. **Threshold Tuning**: Adjust `SIMILARITY_THRESHOLD` berdasarkan testing

### Security Notes

- API ini **TIDAK menggunakan authentication/authorization**
- Untuk production, tambahkan JWT/OAuth2
- Lindungi dengan API Gateway atau reverse proxy
- Gunakan HTTPS untuk transmission data
- Implement rate limiting untuk prevent abuse

---

## 📄 License

MIT License

## 👨‍💻 Development

- **Version**: 3.0.1
- **Last Updated**: November 27, 2025
- **Integration**: Laravel SILAB Database
- **Recent Fixes**:
  - Fixed `absensi` table structure (removed `user_id` column dependency)
  - Added proper relationship: `absensi -> jadwal_piket -> user`
  - Fixed `/api/piket/mulai` and `/api/piket/akhiri` endpoints
  - Added validation for jadwal_piket and periode_piket
  - Changed `is_active` to `isactive` to match database schema

---

## 🔗 Resources

- [FaceNet Paper](https://arxiv.org/abs/1503.03832)
- [keras-facenet Documentation](https://github.com/nyoki-mtl/keras-facenet)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [OpenCV Documentation](https://docs.opencv.org/)

---

## 🙏 Acknowledgments

- FaceNet model by Google
- keras-facenet by nyoki-mtl
- SILAB Database Structure

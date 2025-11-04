# API Absensi Piket Lab - Face Recognition System

API RESTful untuk sistem absensi piket laboratorium menggunakan teknologi Face Recognition dengan FaceNet. Sistem ini dilengkapi dengan autentikasi JWT, multiple photo capture, dan real-time face verification.

## 🎯 Fitur Utama

### Autentikasi & Keamanan
- ✅ **JWT Authentication** - Token-based security dengan expiry 1 jam
- ✅ **Password Hashing** - Bcrypt encryption untuk keamanan password
- ✅ **Face Recognition Login** - Login menggunakan wajah + password

### Manajemen Anggota
- ✅ **Insert Anggota** - Daftar anggota baru dengan 20 foto wajah
- ✅ **Update Face Vectors** - Perbarui embedding wajah (20 foto)
- ✅ **Face Recognition** - Dry run testing untuk debugging

### Absensi Piket
- ✅ **Mulai Piket** - Real-time face recognition (1 foto)
- ✅ **Akhiri Piket** - Real-time verification dengan input kegiatan
- ✅ **Durasi Otomatis** - Perhitungan durasi piket otomatis
- ✅ **Riwayat Absensi** - Filter berdasarkan tanggal, anggota, dan status

## 🛠️ Teknologi

| Komponen | Teknologi | Versi |
|----------|-----------|-------|
| Framework | Flask | 3.0+ |
| Face Recognition | FaceNet (keras-facenet) | 0.3.2 |
| Deep Learning | TensorFlow | 2.15+ |
| Computer Vision | OpenCV | 4.9+ |
| Database | MySQL | 8.0+ |
| ORM | SQLAlchemy | 3.1+ |
| Authentication | PyJWT | 2.8+ |
| Password Hashing | bcrypt | 4.1+ |

## 📋 Struktur Database

### Tabel: `anggota`
```sql
CREATE TABLE anggota (
    id_anggota VARCHAR(20) PRIMARY KEY,
    nama VARCHAR(100) NOT NULL,
    divisi VARCHAR(50),
    no_hp VARCHAR(15),
    password VARCHAR(255) NOT NULL,
    path_wajah VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Tabel: `vektor_wajah`
```sql
CREATE TABLE vektor_wajah (
    id_vektor_wajah INT PRIMARY KEY AUTO_INCREMENT,
    id_anggota VARCHAR(20) NOT NULL,
    vektor JSON NOT NULL,  -- 512-dimensional FaceNet embedding
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_anggota) REFERENCES anggota(id_anggota) 
        ON UPDATE CASCADE ON DELETE CASCADE
);
```

### Tabel: `absensi`
```sql
CREATE TABLE absensi (
    id CHAR(36) PRIMARY KEY,  -- UUID
    id_anggota VARCHAR(20) NOT NULL,
    tanggal DATE NOT NULL,
    jam_masuk TIME NOT NULL,
    jam_keluar TIME,
    foto VARCHAR(255),
    kegiatan TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (id_anggota) REFERENCES anggota(id_anggota)
        ON UPDATE CASCADE ON DELETE CASCADE,
    UNIQUE KEY unique_attendance_per_day (id_anggota, tanggal)
);
```

**Catatan Penting:**
- Model lama `absen_piket` sudah **DEPRECATED**
- Gunakan tabel `absensi` untuk semua operasi baru
- DDL lengkap tersedia di `database_absensi_ddl.sql`

## 🚀 Instalasi

### 1. Prerequisites
- Python 3.8 atau lebih tinggi
- MySQL 8.0 atau lebih tinggi
- Git (optional)

### 2. Clone atau Download Project

```bash
git clone https://github.com/Benni2013/api-piket.git
cd api-piket/api-piket
```

### 3. Buat Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```powershell
pip install -r requirements.txt
```

**Dependencies yang akan terinstall:**
- Flask 3.0.3
- keras-facenet 0.3.2
- TensorFlow 2.15.0
- OpenCV-Python 4.9.0.80
- PyMySQL 1.1.1
- SQLAlchemy 3.1.1
- PyJWT 2.8.0
- bcrypt 4.1.3
- Flask-CORS 4.0.1

### 5. Setup Database

**Buat database:**
```sql
CREATE DATABASE api_piket CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

**Import struktur database:**
```bash
mysql -u root -p api_piket < database_absensi_ddl.sql
```

### 6. Konfigurasi Environment

Copy file `.env.example` ke `.env`:
```powershell
copy .env.example .env
```

Edit file `.env`:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=api_piket

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
PORT=5000

# JWT Configuration (optional, defaults in app.py)
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION=3600

# Face Recognition Configuration
FACE_THRESHOLD=0.7

# Upload Configuration
UPLOAD_FOLDER=data/wajah

# CORS Configuration
CORS_ORIGINS=http://localhost:8000,http://localhost:3000
```

### 7. Jalankan Aplikasi

```powershell
python app.py
```

API akan berjalan di: **http://localhost:5000**

Cek health status:
```powershell
curl http://localhost:5000/health
```

## 📚 API Documentation

### Base URL
```
http://localhost:5000
```

### Authentication
Sebagian besar endpoint membutuhkan JWT token di header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🔐 1. Authentication Endpoints

### 1.1 Login dengan Face Recognition

**POST** `/api/auth/login`

**Request Body:**
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response (Success):**
```json
{
    "success": true,
    "message": "Login berhasil! Selamat datang, Benni",
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "data": {
        "id_anggota": "RDBI.I.01",
        "nama": "Benni",
        "divisi": "Web Development",
        "similarity": 0.952
    }
}
```

**Response (Failed):**
```json
{
    "success": false,
    "message": "Wajah tidak dikenali. Pastikan Anda sudah terdaftar."
}
```

---

## 👥 2. Face Management Endpoints

### 2.1 Insert Anggota Baru (20 Foto)

**POST** `/api/face/insert`

**Auth:** None required

**Request Body:**
```json
{
    "id_anggota": "RDBI.I.01",
    "nama": "Benni",
    "divisi": "Web Development",
    "no_hp": "081234567890",
    "password": "password123",
    "images": [
        "data:image/jpeg;base64,/9j/4AAQ...",
        "data:image/jpeg;base64,/9j/4AAQ...",
        "... (18 more images)"
    ]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Anggota Benni berhasil ditambahkan!",
    "data": {
        "id_anggota": "RDBI.I.01",
        "nama": "Benni",
        "divisi": "Web Development",
        "vectors_count": 20,
        "path_wajah": "data/wajah/RDBI.I.01_Benni"
    }
}
```

### 2.2 Update Face Vectors (20 Foto)

**PUT** `/api/face/update/<id_anggota>`

**Auth:** Required (Bearer Token)

**Request Body:**
```json
{
    "images": [
        "data:image/jpeg;base64,/9j/4AAQ...",
        "... (19 more images)"
    ]
}
```

### 2.3 Face Recognition (Dry Run)

**POST** `/api/face/recognize`

**Auth:** Required

**Request Body:**
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
    "success": true,
    "match": true,
    "data": {
        "id_anggota": "RDBI.I.01",
        "nama": "Benni",
        "similarity": 0.945
    }
}
```

---

## ⏰ 3. Piket Operations

### 3.1 Mulai Piket (Real-time, 1 Foto)

**POST** `/api/piket/mulai`

**Auth:** Required

**Request Body:**
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
    "success": true,
    "message": "Piket dimulai! Selamat datang, Benni",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "id_anggota": "RDBI.I.01",
        "nama": "Benni",
        "divisi": "Web Development",
        "tanggal": "2025-11-04",
        "jam_masuk": "08:30:15"
    }
}
```

**Catatan:**
- Hanya bisa 1x per hari per anggota
- Wajah harus sesuai dengan akun login

### 3.2 Akhiri Piket (Real-time, 1 Foto)

**POST** `/api/piket/akhiri`

**Auth:** Required

**Request Body:**
```json
{
    "kegiatan": "Maintenance server, update dokumentasi, development fitur baru",
    "image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

**Response:**
```json
{
    "success": true,
    "message": "Piket selesai! Terima kasih, Benni",
    "data": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "id_anggota": "RDBI.I.01",
        "nama": "Benni",
        "tanggal": "2025-11-04",
        "jam_masuk": "08:30:15",
        "jam_keluar": "16:45:30",
        "durasi": "8 jam 15 menit",
        "kegiatan": "Maintenance server, update dokumentasi..."
    }
}
```

---

## 📊 4. Data Retrieval Endpoints

### 4.1 Get All Anggota

**GET** `/api/anggota`

**Auth:** Required

**Query Parameters:**
- `id_anggota` (optional): Filter by ID
- `divisi` (optional): Filter by divisi

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id_anggota": "RDBI.I.01",
            "nama": "Benni",
            "divisi": "Web Development",
            "no_hp": "081234567890",
            "path_wajah": "data/wajah/RDBI.I.01_Benni",
            "created_at": "2025-11-04T08:00:00",
            "updated_at": "2025-11-04T08:00:00"
        }
    ],
    "count": 1
}
```

### 4.2 Get Absensi

**GET** `/api/absensi`

**Auth:** Required

**Query Parameters:**
- `tanggal` (optional, default: today): Format YYYY-MM-DD
- `id_anggota` (optional): Filter by ID
- `status` (optional): "aktif" atau "selesai"

**Response:**
```json
{
    "success": true,
    "data": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "id_anggota": "RDBI.I.01",
            "nama": "Benni",
            "divisi": "Web Development",
            "tanggal": "2025-11-04",
            "jam_masuk": "08:30:15",
            "jam_keluar": "16:45:30",
            "durasi": "8 jam 15 menit",
            "foto": "data/wajah/RDBI.I.01_Benni/20251104_083015.jpg",
            "kegiatan": "Maintenance server...",
            "created_at": "2025-11-04T08:30:15",
            "updated_at": "2025-11-04T16:45:30"
        }
    ],
    "count": 1,
    "tanggal": "2025-11-04"
}
```

**Filter Examples:**
```bash
# Today's attendance
GET /api/absensi

# Specific date
GET /api/absensi?tanggal=2025-11-04

# By member
GET /api/absensi?id_anggota=RDBI.I.01

# Active piket (not finished yet)
GET /api/absensi?status=aktif

# Completed piket
GET /api/absensi?status=selesai
```

---

## 🔧 Utility Tools

### 1. `image_to_base64.py` - Image Converter

Tool untuk convert image ke base64 string (berguna untuk testing).

**Usage:**
```powershell
# Interactive mode
python image_to_base64.py

# Command line mode
python image_to_base64.py foto.jpg

# Save to file
python image_to_base64.py foto.jpg output.txt
```

**Fitur:**
- Convert JPG, PNG, GIF ke base64
- Include data URI header otomatis
- Save to file atau copy to clipboard
- Preview output

### 2. Postman Collection

File: `API_Absen_Piket.postman_collection.json`

**⚠️ Catatan:** Jika tidak menggunakan Postman, file ini **boleh dihapus**.

Untuk import di Postman:
1. Buka Postman
2. Click Import
3. Select file `API_Absen_Piket.postman_collection.json`
4. Set environment variable `base_url` = `http://localhost:5000`

---

## ⚙️ Konfigurasi Lanjutan

### Face Recognition Threshold

Default threshold: **0.7** (70% similarity)

Untuk mengubah, edit di method call:
```python
result = face_service.find_best_match_from_db(
    embedding, 
    db.session, 
    threshold=0.6  # Lower = more permissive
)
```

**Rekomendasi:**
- `0.7` - Standar (balanced)
- `0.6` - Lebih permisif (untuk lighting/angle yang berbeda)
- `0.8` - Lebih strict (untuk keamanan tinggi)

### Upload Folder Structure

```
data/
└── wajah/
    ├── RDBI.I.01_Benni/
    │   ├── 20251104_083015_1.jpg
    │   ├── 20251104_083015_2.jpg
    │   └── ... (18 more)
    └── tes1_tes/
        └── ... (20 images)
```

### CORS Configuration

Edit di `app.py`:
```python
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8000", "https://yourdomain.com"]
    }
})
```

---

## 🐛 Troubleshooting

### Database Connection Error
```
sqlalchemy.exc.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solusi:**
1. Pastikan MySQL service running
2. Cek kredensial di `.env`
3. Verify database sudah dibuat: `CREATE DATABASE api_piket;`

### Face Not Detected
```
{"success": false, "message": "Wajah tidak terdeteksi"}
```

**Solusi:**
1. Pastikan pencahayaan cukup
2. Wajah harus menghadap kamera langsung
3. Gunakan resolusi minimal 640x480
4. Hindari kacamata/masker

### No Match Found
```
{"success": false, "message": "Wajah tidak dikenali"}
```

**Solusi:**
1. Cek data embedding di database: `SELECT COUNT(*) FROM vektor_wajah;`
2. Pastikan sudah insert/update dengan 20 foto
3. Coba turunkan threshold dari 0.7 ke 0.6
4. Lihat log Flask untuk similarity score

### Import Error
```
ModuleNotFoundError: No module named 'keras_facenet'
```

**Solusi:**
```powershell
pip install -r requirements.txt
```

### JWT Token Expired
```
{"success": false, "message": "Token expired"}
```

**Solusi:**
- Token berlaku 1 jam, login ulang untuk mendapat token baru

---

## 📁 Struktur Project

```
api-piket/
├── app.py                          # Main Flask application
├── config.py                       # Database & Flask config
├── models.py                       # SQLAlchemy ORM models
├── face_recognition.py             # FaceNet service
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (gitignored)
├── .env.example                   # Environment template
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
├── database_absensi_ddl.sql       # Database schema
├── image_to_base64.py             # Utility: Image converter
├── API_Absen_Piket.postman_collection.json  # Postman tests (optional)
├── __pycache__/                   # Python cache (gitignored)
└── data/
    └── wajah/                     # Face images storage
        ├── RDBI.I.01_Benni/
        └── tes1_tes/
```

---

## 🔒 Security Best Practices

1. **Ganti Secret Keys**
   - Ubah `SECRET_KEY` dan `JWT_SECRET_KEY` di production
   - Gunakan random string minimal 32 karakter

2. **Database Credentials**
   - Jangan commit file `.env` ke Git
   - Gunakan user database dengan privilege terbatas

3. **Password Policy**
   - Minimal 8 karakter
   - Password di-hash dengan bcrypt (cost factor 12)

4. **CORS Configuration**
   - Hanya izinkan domain yang dipercaya
   - Hindari wildcard `*` di production

5. **File Upload**
   - Validasi file type (hanya JPG, PNG)
   - Limit file size (max 10MB per image)

---

## 📊 Performance Tips

1. **Database Indexing**
   - Index sudah ada di: `id_anggota`, `tanggal`
   - Monitor slow query dengan `EXPLAIN`

2. **Face Recognition**
   - Batch processing untuk multiple images
   - Cache embeddings di memory (optional)

3. **Image Storage**
   - Compress images sebelum save (quality 85%)
   - Pertimbangkan CDN untuk production

---

## 📝 Changelog

### Version 2.0.0 (2025-11-04)
- ✅ JWT Authentication system
- ✅ New database structure (`absensi` table)
- ✅ Password hashing with bcrypt
- ✅ Durasi calculation automatic
- ✅ Status filter (aktif/selesai)
- ⚠️ Deprecated `absen_piket` model

### Version 1.0.0 (2025-10-27)
- ✅ Initial release
- ✅ Basic face recognition
- ✅ Insert/Update endpoints
- ✅ Mulai/Akhiri piket

---

## 🤝 Contributing

1. Fork repository
2. Buat branch baru: `git checkout -b feature/AmazingFeature`
3. Commit changes: `git commit -m 'Add some AmazingFeature'`
4. Push to branch: `git push origin feature/AmazingFeature`
5. Open Pull Request

---

## 📄 License

MIT License - see LICENSE file for details

---

## 👨‍💻 Author

**Benni**
- GitHub: [@Benni2013](https://github.com/Benni2013)
- Project: [api-piket](https://github.com/Benni2013/api-piket)

---

## 🆘 Support

Jika ada pertanyaan atau masalah:
1. Cek section [Troubleshooting](#-troubleshooting)
2. Lihat log Flask untuk error detail
3. Open issue di GitHub repository

---

**Last Updated:** November 4, 2025
**Last Updated:** November 4, 2025

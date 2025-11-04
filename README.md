# API Pengenalan Wajah untuk Absen Piket Lab

API untuk sistem absensi piket laboratorium menggunakan pengenalan wajah dengan FaceNet.

## Fitur

- **Insert Data Wajah**: Menambahkan data anggota dan vektor wajah ke database
- **Mulai Piket**: Absensi mulai piket dengan pengenalan wajah
- **Akhiri Piket**: Absensi akhir piket dengan pengenalan wajah
- **Get Data Anggota**: Mengambil daftar anggota
- **Get Data Absensi**: Mengambil data absensi berdasarkan tanggal

## Teknologi

- **Flask**: Web framework
- **FaceNet**: Model deep learning untuk face recognition
- **MySQL**: Database
- **OpenCV**: Image processing
- **SQLAlchemy**: ORM untuk database

## Instalasi

### 1. Clone atau Download Project

```bash
cd api-piket/api
```

### 2. Buat Virtual Environment (Recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Konfigurasi Database

Buat database MySQL:

```sql
CREATE DATABASE absen_apm;
```

Salin file `.env.example` menjadi `.env` dan sesuaikan konfigurasi:

```powershell
copy .env.example .env
```

Edit file `.env`:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=absen_apm
SECRET_KEY=your-secret-key-change-this
```

### 5. Jalankan Aplikasi

```powershell
python app.py
```

API akan berjalan di `http://localhost:5000`

## Struktur Database

### Tabel: anggota
- `id_anggota` (VARCHAR 20, PK)
- `nama` (VARCHAR 100)
- `divisi` (VARCHAR 50)
- `path_wajah` (VARCHAR 255)
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

### Tabel: vektor_wajah
- `id_vektor_wajah` (INT, PK, AUTO_INCREMENT)
- `id_anggota` (VARCHAR 20, FK)
- `vektor` (JSON) - 512 dimensi embedding FaceNet
- `created_at` (DATETIME)

### Tabel: absen_piket
- `id` (INT, PK, AUTO_INCREMENT)
- `id_anggota` (VARCHAR 20, FK)
- `tanggal` (DATE)
- `waktu` (TIME)
- `status` (ENUM: 'Hadir', 'Tidak Hadir', 'Terlambat')
- `jenis` (ENUM: 'Mulai', 'Akhir')
- `created_at` (DATETIME)

## API Endpoints

### 1. Health Check

**GET** `/health`

Response:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2025-10-27T10:00:00"
}
```

### 2. Insert Data Wajah

**POST** `/api/face/insert`

Request Body:
```json
{
  "id_anggota": "RDBI.I.01",
  "nama": "Nama Anggota",
  "divisi": "Web Development",
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "additional_images": [
    "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
    "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
  ]
}
```

Response (Success):
```json
{
  "success": true,
  "message": "Anggota Nama Anggota berhasil ditambahkan dengan 3 vektor wajah!",
  "data": {
    "id_anggota": "RDBI.I.01",
    "nama": "Nama Anggota",
    "divisi": "Web Development",
    "total_vectors": 3
  }
}
```

### 3. Mulai Piket

**POST** `/api/piket/mulai`

Request Body:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

Response (Success):
```json
{
  "success": true,
  "message": "Selamat datang, Nama Anggota! Piket dimulai.",
  "data": {
    "id_anggota": "RDBI.I.01",
    "nama": "Nama Anggota",
    "divisi": "Web Development",
    "tanggal": "2025-10-27",
    "waktu": "08:30:15",
    "status": "Hadir",
    "jenis": "Mulai",
    "confidence": "0.89"
  }
}
```

### 4. Akhiri Piket

**POST** `/api/piket/akhiri`

Request Body:
```json
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

Response (Success):
```json
{
  "success": true,
  "message": "Terima kasih, Nama Anggota! Piket selesai.",
  "data": {
    "id_anggota": "RDBI.I.01",
    "nama": "Nama Anggota",
    "divisi": "Web Development",
    "tanggal": "2025-10-27",
    "waktu_mulai": "08:30:15",
    "waktu_akhir": "17:00:30",
    "status": "Hadir",
    "jenis": "Akhir",
    "confidence": "0.91"
  }
}
```

### 5. Get Data Anggota

**GET** `/api/anggota`

Query Parameters:
- `id_anggota` (optional): Filter by ID
- `divisi` (optional): Filter by divisi

Response:
```json
{
  "success": true,
  "data": [
    {
      "id_anggota": "RDBI.I.01",
      "nama": "Nama Anggota",
      "divisi": "Web Development",
      "path_wajah": "RDBI.I.01_Nama Anggota/20251027083015.jpg",
      "created_at": "2025-10-27T08:30:15",
      "updated_at": "2025-10-27T08:30:15"
    }
  ],
  "count": 1
}
```

### 6. Get Data Absensi

**GET** `/api/absensi`

Query Parameters:
- `tanggal` (optional, default: today): Format YYYY-MM-DD
- `id_anggota` (optional): Filter by ID
- `jenis` (optional): Filter by jenis (Mulai/Akhir)

Response:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "id_anggota": "RDBI.I.01",
      "nama": "Nama Anggota",
      "divisi": "Web Development",
      "tanggal": "2025-10-27",
      "waktu": "08:30:15",
      "status": "Hadir",
      "jenis": "Mulai",
      "created_at": "2025-10-27T08:30:15"
    }
  ],
  "count": 1,
  "tanggal": "2025-10-27"
}
```

## Testing dengan curl

### Insert Face Data
```powershell
curl -X POST http://localhost:5000/api/face/insert `
  -H "Content-Type: application/json" `
  -d '{\"id_anggota\":\"TEST.01\",\"nama\":\"Test User\",\"divisi\":\"Testing\",\"image\":\"BASE64_IMAGE_HERE\"}'
```

### Mulai Piket
```powershell
curl -X POST http://localhost:5000/api/piket/mulai `
  -H "Content-Type: application/json" `
  -d '{\"image\":\"BASE64_IMAGE_HERE\"}'
```

### Akhiri Piket
```powershell
curl -X POST http://localhost:5000/api/piket/akhiri `
  -H "Content-Type: application/json" `
  -d '{\"image\":\"BASE64_IMAGE_HERE\"}'
```

### Get Anggota
```powershell
curl http://localhost:5000/api/anggota
```

### Get Absensi
```powershell
curl http://localhost:5000/api/absensi?tanggal=2025-10-27
```

## Konfigurasi

### Face Recognition Threshold
Default threshold untuk pengenalan wajah adalah 0.7 (70% similarity).
Dapat diubah di file `.env`:

```
FACE_THRESHOLD=0.7
```

### CORS Configuration
Untuk mengizinkan akses dari domain tertentu, edit di `.env`:

```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

## Error Handling

API akan mengembalikan response dengan format:

```json
{
  "success": false,
  "message": "Error message here"
}
```

HTTP Status Codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

## Development

### Struktur File
```
api/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── models.py             # Database models
├── face_recognition.py   # Face recognition service
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables example
├── .gitignore           # Git ignore rules
├── README.md            # Documentation
└── data/                # Upload folder (auto-created)
    └── wajah/          # Face images storage
```

### Environment Variables
- `FLASK_ENV`: development/production
- `DB_HOST`: Database host
- `DB_PORT`: Database port
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `SECRET_KEY`: Flask secret key
- `FACE_THRESHOLD`: Face recognition threshold
- `UPLOAD_FOLDER`: Upload directory path
- `CORS_ORIGINS`: Allowed CORS origins
- `PORT`: Server port

## Troubleshooting

### Database Connection Error
- Pastikan MySQL service berjalan
- Cek kredensial database di file `.env`
- Pastikan database sudah dibuat

### Face Not Detected
- Pastikan pencahayaan cukup
- Wajah harus menghadap kamera
- Gunakan gambar dengan resolusi yang baik

### Import Error
- Pastikan semua dependencies terinstall: `pip install -r requirements.txt`
- Gunakan virtual environment

## License

MIT License

## Author

API Absen Piket Lab

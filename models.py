"""
Database Models untuk API Absen Piket
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Anggota(db.Model):
    """Model untuk tabel anggota"""
    __tablename__ = 'anggota'
    
    id_anggota = db.Column(db.String(20), primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    divisi = db.Column(db.String(50), nullable=False)
    path_wajah = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=True)  # For login
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime, 
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    # Relasi
    vektor_wajah = db.relationship('VektorWajah', backref='anggota', 
                                     cascade='all, delete-orphan', lazy=True)
    absensi = db.relationship('Absensi', backref='anggota', 
                              cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id_anggota': self.id_anggota,
            'nama': self.nama,
            'divisi': self.divisi,
            'path_wajah': self.path_wajah,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class VektorWajah(db.Model):
    """Model untuk tabel vektor_wajah"""
    __tablename__ = 'vektor_wajah'
    
    id_vektor_wajah = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_anggota = db.Column(
        db.String(20), 
        db.ForeignKey('anggota.id_anggota', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    vektor = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id_vektor_wajah': self.id_vektor_wajah,
            'id_anggota': self.id_anggota,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# DEPRECATED MODEL - DO NOT USE
# =============================================================================
# class AbsenPiket(db.Model):
#     """Model untuk tabel absen_piket - DEPRECATED, gunakan Absensi"""
#     __tablename__ = 'absen_piket'
#     
#     id = db.Column(db.Integer, primary_key=True, autoincrement=True)
#     id_anggota = db.Column(
#         db.String(20),
#         db.ForeignKey('anggota.id_anggota', onupdate='CASCADE', ondelete='CASCADE'),
#         nullable=False
#     )
#     tanggal = db.Column(db.Date, nullable=False)
#     waktu = db.Column(db.Time, nullable=False)
#     status = db.Column(
#         db.Enum('Hadir', 'Tidak Hadir', 'Terlambat'),
#         nullable=False
#     )
#     jenis = db.Column(
#         db.Enum('Mulai', 'Akhir'),
#         nullable=False,
#         default='Mulai'
#     )
#     created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
#     
#     __table_args__ = (
#         db.UniqueConstraint('id_anggota', 'tanggal', 'jenis', 
#                            name='unique_attendance_per_type'),
#     )
#     
#     def to_dict(self):
#         """Konversi object ke dictionary"""
#         return {
#             'id': self.id,
#             'id_anggota': self.id_anggota,
#             'nama': self.anggota.nama if self.anggota else None,
#             'divisi': self.anggota.divisi if self.anggota else None,
#             'tanggal': self.tanggal.isoformat() if self.tanggal else None,
#             'waktu': self.waktu.strftime('%H:%M:%S') if self.waktu else None,
#             'status': self.status,
#             'jenis': self.jenis,
#             'created_at': self.created_at.isoformat() if self.created_at else None
#         }
# =============================================================================


class Absensi(db.Model):
    """Model untuk tabel absensi - Struktur baru sesuai requirement"""
    __tablename__ = 'absensi'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    id_anggota = db.Column(
        db.String(20),
        db.ForeignKey('anggota.id_anggota', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    tanggal = db.Column(db.Date, nullable=False)
    jam_masuk = db.Column(db.Time, nullable=True)
    jam_keluar = db.Column(db.Time, nullable=True)
    foto = db.Column(db.String(255), nullable=True)
    jadwal_piket = db.Column(db.String(36), nullable=True)  # Diabaikan untuk saat ini
    kegiatan = db.Column(db.Text, nullable=True)
    periode_piket = db.Column(db.String(36), nullable=True)  # Diabaikan untuk saat ini
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    __table_args__ = (
        db.UniqueConstraint('id_anggota', 'tanggal',
                           name='unique_anggota_tanggal'),
    )
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        # Calculate duration if both jam_masuk and jam_keluar exist
        durasi = None
        if self.jam_masuk and self.jam_keluar:
            from datetime import datetime, timedelta
            dt_masuk = datetime.combine(self.tanggal, self.jam_masuk)
            dt_keluar = datetime.combine(self.tanggal, self.jam_keluar)
            delta = dt_keluar - dt_masuk
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            durasi = f"{hours} jam {minutes} menit"
        
        return {
            'id': self.id,
            'id_anggota': self.id_anggota,
            'nama': self.anggota.nama if self.anggota else None,
            'divisi': self.anggota.divisi if self.anggota else None,
            'tanggal': self.tanggal.isoformat() if self.tanggal else None,
            'jam_masuk': self.jam_masuk.strftime('%H:%M:%S') if self.jam_masuk else None,
            'jam_keluar': self.jam_keluar.strftime('%H:%M:%S') if self.jam_keluar else None,
            'durasi': durasi,
            'foto': self.foto,
            'kegiatan': self.kegiatan,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


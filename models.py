"""
Database Models untuk API Piket - Integrasi dengan Database SILAB
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# =============================================================================
# Models dari Database SILAB (Read-Only, tidak dibuat oleh API ini)
# =============================================================================

class Users(db.Model):
    """Model untuk tabel users dari database SILAB"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    email_verified_at = db.Column(db.DateTime, nullable=True)
    password = db.Column(db.String(255), nullable=False)
    remember_token = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    
    # Relasi - TIDAK pakai backref di sini, backref didefinisikan di model target
    # Ini hanya untuk akses forward relationship dari Users
    # profile = db.relationship('Profile', uselist=False, lazy=True)
    # vektor_wajah = db.relationship('VektorWajah', cascade='all, delete-orphan', lazy=True)
    # jadwal_piket = db.relationship('JadwalPiket', cascade='all, delete-orphan', lazy=True)
    # absensi = db.relationship('Absensi', cascade='all, delete-orphan', lazy=True)
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Profile(db.Model):
    """Model untuk tabel profile dari database SILAB"""
    __tablename__ = 'profile'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    nomor_induk = db.Column(db.String(255), nullable=False)
    jenis_kelamin = db.Column(db.Enum('laki-laki', 'perempuan'), nullable=False)
    foto_profile = db.Column(db.String(255), nullable=True)
    alamat = db.Column(db.String(255), nullable=True)
    no_hp = db.Column(db.String(255), nullable=True)
    tempat_lahir = db.Column(db.String(255), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=True)
    nomor_anggota = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    
    # Backref untuk akses dari Users -> Profile (users.profile)
    user = db.relationship('Users', backref=db.backref('profile', uselist=False, lazy=True))
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nomor_induk': self.nomor_induk,
            'jenis_kelamin': self.jenis_kelamin,
            'foto_profile': self.foto_profile,
            'alamat': self.alamat,
            'no_hp': self.no_hp,
            'tempat_lahir': self.tempat_lahir,
            'tanggal_lahir': self.tanggal_lahir.isoformat() if self.tanggal_lahir else None,
            'nomor_anggota': self.nomor_anggota,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class JadwalPiket(db.Model):
    """Model untuk tabel jadwal_piket dari database SILAB"""
    __tablename__ = 'jadwal_piket'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    hari = db.Column(db.String(255), nullable=False)
    kepengurusan_lab_id = db.Column(db.String(36), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    
    # Backref untuk akses dari Users -> JadwalPiket (users.jadwal_piket)
    user = db.relationship('Users', backref=db.backref('jadwal_piket', cascade='all, delete-orphan', lazy=True))
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'hari': self.hari,
            'kepengurusan_lab_id': self.kepengurusan_lab_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PeriodePiket(db.Model):
    """Model untuk tabel periode_piket dari database SILAB"""
    __tablename__ = 'periode_piket'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    kepengurusan_lab_id = db.Column(db.String(36), nullable=False)
    nama = db.Column(db.String(255), nullable=False)
    tanggal_mulai = db.Column(db.Date, nullable=False)
    tanggal_selesai = db.Column(db.Date, nullable=False)
    isactive = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id': self.id,
            'kepengurusan_lab_id': self.kepengurusan_lab_id,
            'nama': self.nama,
            'tanggal_mulai': self.tanggal_mulai.isoformat() if self.tanggal_mulai else None,
            'tanggal_selesai': self.tanggal_selesai.isoformat() if self.tanggal_selesai else None,
            'isactive': self.isactive,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# =============================================================================
# Models yang Dikelola oleh API Piket
# =============================================================================

class VektorWajah(db.Model):
    """Model untuk tabel vektor_wajah - Dikelola oleh API Piket"""
    __tablename__ = 'vektor_wajah'
    
    id_vektor_wajah = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.String(36), 
        db.ForeignKey('users.id', onupdate='CASCADE', ondelete='CASCADE'),
        nullable=False
    )
    vektor = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    # Backref untuk akses dari Users -> VektorWajah (users.vektor_wajah)
    user = db.relationship('Users', backref=db.backref('vektor_wajah', cascade='all, delete-orphan', lazy=True))
    
    def to_dict(self):
        """Konversi object ke dictionary"""
        return {
            'id_vektor_wajah': self.id_vektor_wajah,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }




class Absensi(db.Model):
    """Model untuk tabel absensi dari database SILAB - Dikelola oleh API Piket"""
    __tablename__ = 'absensi'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    tanggal = db.Column(db.Date, nullable=False)
    jam_masuk = db.Column(db.Time, nullable=False)
    jam_keluar = db.Column(db.Time, nullable=True)
    foto = db.Column(db.String(255), nullable=False, default='')
    jadwal_piket = db.Column(db.String(36), db.ForeignKey('jadwal_piket.id'), nullable=False)
    kegiatan = db.Column(db.Text, nullable=False, default='')
    periode_piket_id = db.Column(db.String(36), db.ForeignKey('periode_piket.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp()
    )
    
    # Relasi ke JadwalPiket dan PeriodePiket
    # Akses user melalui jadwal_piket_rel.user
    jadwal_piket_rel = db.relationship('JadwalPiket', foreign_keys=[jadwal_piket], 
                                       backref=db.backref('absensi_list', lazy=True))
    periode = db.relationship('PeriodePiket', foreign_keys=[periode_piket_id], 
                             backref=db.backref('absensi_periode', lazy=True))
    
    def get_user_id(self):
        """Get user_id from jadwal_piket relationship"""
        if self.jadwal_piket_rel:
            return self.jadwal_piket_rel.user_id
        return None
    
    def get_user(self):
        """Get user object from jadwal_piket relationship"""
        if self.jadwal_piket_rel:
            return self.jadwal_piket_rel.user
        return None
    
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
        
        user = self.get_user()
        
        return {
            'id': self.id,
            'user_id': self.get_user_id(),
            'name': user.name if user else None,
            'tanggal': self.tanggal.isoformat() if self.tanggal else None,
            'jam_masuk': self.jam_masuk.strftime('%H:%M:%S') if self.jam_masuk else None,
            'jam_keluar': self.jam_keluar.strftime('%H:%M:%S') if self.jam_keluar else None,
            'durasi': durasi,
            'foto': self.foto,
            'kegiatan': self.kegiatan,
            'jadwal_piket': self.jadwal_piket,
            'periode_piket_id': self.periode_piket_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


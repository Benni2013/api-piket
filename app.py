"""
API Pengenalan Wajah untuk Absen Piket Lab
Menggunakan FaceNet untuk face recognition
"""
import os
import uuid
import jwt
from datetime import datetime, date, time, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd

from config import config_by_name
from models import db, Anggota, VektorWajah, Absensi
from face_recognition import FaceRecognitionService


# JWT Configuration
JWT_SECRET_KEY = 'your-secret-key-change-in-production'
JWT_EXPIRATION = 3600  # 1 hour


def create_token(id_anggota):
    """Generate JWT token"""
    payload = {
        'id_anggota': id_anggota,
        'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')


def verify_token(token):
    """Verify JWT token and return id_anggota"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload['id_anggota']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    """Decorator untuk endpoint yang membutuhkan authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'message': 'Missing or invalid authorization header'
            }), 401
        
        token = auth_header.replace('Bearer ', '')
        id_anggota = verify_token(token)
        
        if not id_anggota:
            return jsonify({
                'success': False,
                'message': 'Invalid or expired token'
            }), 401
        
        # Store current user in request context
        request.current_user = id_anggota
        return f(*args, **kwargs)
    
    return decorated_function


def create_app(config_name='development'):
    """Factory function untuk membuat Flask app"""
    app = Flask(__name__)
    
    # Load konfigurasi
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize face recognition service
    face_service = FaceRecognitionService()
    
    # Buat folder upload jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Routes
    @app.route('/', methods=['GET'])
    def index():
        """Root endpoint"""
        return jsonify({
            'message': 'API Absen Piket Lab',
            'version': '2.0.0',
            'endpoints': {
                'health': '/health',
                'login': '/api/auth/login',
                'recognize': '/api/face/recognize',
                'insert_face': '/api/face/insert',
                'update_face': '/api/face/update/<id_anggota>',
                'mulai_piket': '/api/piket/mulai',
                'akhiri_piket': '/api/piket/akhiri',
                'get_anggota': '/api/anggota',
                'get_absensi': '/api/absensi'
            }
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'ok',
            'database': db_status,
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        """
        Login dengan face recognition
        
        Request Body (JSON):
        {
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true,
            "message": "Login berhasil",
            "token": "jwt_token_here",
            "data": {
                "id_anggota": "...",
                "nama": "...",
                "divisi": "..."
            }
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            # Get image
            image_base64 = data.get('image', '').strip()
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image wajib diisi'
                }), 400
            
            # Decode image
            try:
                img = face_service.decode_base64_image(image_base64)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid image format: {str(e)}'
                }), 400
            
            # Extract embedding
            try:
                embedding = face_service.extract_embedding(img)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Wajah tidak terdeteksi: {str(e)}'
                }), 400
            
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak terdeteksi. Pastikan wajah Anda terlihat jelas.'
                }), 400
            
            # Find best match from database
            result = face_service.find_best_match_from_db(embedding, db.session)
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenali. Pastikan Anda sudah terdaftar.'
                }), 401
            
            # Generate token
            token = create_token(result['id_anggota'])
            
            return jsonify({
                'success': True,
                'message': f'Login berhasil! Selamat datang, {result["nama"]}',
                'token': token,
                'data': {
                    'id_anggota': result['id_anggota'],
                    'nama': result['nama'],
                    'divisi': result.get('divisi', '-'),
                    'similarity': result['similarity']
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/face/recognize', methods=['POST'])
    @require_auth
    def recognize_face():
        """
        Dry run face recognition (untuk testing real-time)
        
        Headers:
            Authorization: Bearer <token>
        
        Request Body (JSON):
        {
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true,
            "match": true/false,
            "data": {
                "id_anggota": "...",
                "nama": "...",
                "similarity": 0.95
            }
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            # Get image
            image_base64 = data.get('image', '').strip()
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image wajib diisi'
                }), 400
            
            # Decode image
            try:
                img = face_service.decode_base64_image(image_base64)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid image format: {str(e)}'
                }), 400
            
            # Extract embedding
            try:
                embedding = face_service.extract_embedding(img)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'match': False,
                    'message': 'Wajah tidak terdeteksi'
                }), 200
            
            if embedding is None:
                return jsonify({
                    'success': True,
                    'match': False,
                    'message': 'Wajah tidak terdeteksi'
                }), 200
            
            # Find best match from database
            result = face_service.find_best_match_from_db(embedding, db.session)
            
            if not result:
                return jsonify({
                    'success': True,
                    'match': False,
                    'message': 'Wajah tidak dikenali'
                }), 200
            
            return jsonify({
                'success': True,
                'match': True,
                'data': {
                    'id_anggota': result['id_anggota'],
                    'nama': result['nama'],
                    'divisi': result.get('divisi', '-'),
                    'similarity': result['similarity']
                }
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/face/insert', methods=['POST'])
    def insert_face():
        """
        Insert data anggota dan vektor wajah ke database
        
        Request Body (JSON):
        {
            "id_anggota": "RDBI.I.01",
            "nama": "Nama Anggota",
            "divisi": "Web Development",
            "image": "base64_encoded_image",
            "additional_images": ["base64_image1", "base64_image2", ...]  // Optional
        }
        
        Response:
        {
            "success": true/false,
            "message": "...",
            "data": {...}
        }
        """
        try:
            # Parse request body
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            # Validasi input
            id_anggota = data.get('id_anggota', '').strip()
            nama = data.get('nama', '').strip()
            divisi = data.get('divisi', '').strip()
            
            # Support both single image and multiple images
            image_base64 = data.get('image', '')
            images = data.get('images', [])  # Array of images from camera streaming
            additional_images = data.get('additional_images', [])
            
            if not id_anggota or not nama or not divisi:
                return jsonify({
                    'success': False,
                    'message': 'id_anggota, nama, dan divisi harus diisi!'
                }), 400
            
            # Check if using images array or single image
            if images and len(images) > 0:
                # Multiple images from camera streaming
                if len(images) > 20:
                    return jsonify({
                        'success': False,
                        'message': 'Maximum 20 images!'
                    }), 400
                
                # Use first image as main image, rest as additional
                image_base64 = images[0]
                additional_images = images[1:]
            elif not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image harus disertakan!'
                }), 400
            
            # Cek duplikat ID
            existing = Anggota.query.filter_by(id_anggota=id_anggota).first()
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'ID anggota "{id_anggota}" sudah terdaftar!'
                }), 400
            
            # Decode gambar utama
            img = face_service.decode_base64_image(image_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Format gambar tidak valid!'
                }), 400
            
            # Extract embedding dari gambar utama
            main_embedding = face_service.extract_embedding(img)
            if main_embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Tidak terdeteksi wajah pada gambar!'
                }), 400
            
            # Simpan gambar utama ke disk
            folder = os.path.join(app.config['UPLOAD_FOLDER'], f"{id_anggota}_{nama}")
            os.makedirs(folder, exist_ok=True)
            
            timestamp = pd.Timestamp.now().strftime('%Y%m%d%H%M%S')
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(folder, filename)
            
            if not face_service.save_image(img, filepath):
                return jsonify({
                    'success': False,
                    'message': 'Gagal menyimpan gambar!'
                }), 500
            
            # Path relatif untuk database
            rel_path = os.path.relpath(filepath, app.config['UPLOAD_FOLDER']).replace('\\', '/')
            
            # Simpan data anggota ke database
            anggota = Anggota(
                id_anggota=id_anggota,
                nama=nama,
                divisi=divisi,
                path_wajah=rel_path
            )
            db.session.add(anggota)
            db.session.flush()
            
            # Simpan vektor wajah utama
            vektor = VektorWajah(
                id_anggota=id_anggota,
                vektor=list(map(float, main_embedding))
            )
            db.session.add(vektor)
            
            # Proses gambar tambahan jika ada
            additional_vectors_count = 0
            failed_images = 0
            if additional_images:
                for idx, img_base64 in enumerate(additional_images):
                    try:
                        add_img = face_service.decode_base64_image(img_base64)
                        if add_img is not None:
                            add_embedding = face_service.extract_embedding(add_img)
                            if add_embedding is not None:
                                vektor_add = VektorWajah(
                                    id_anggota=id_anggota,
                                    vektor=list(map(float, add_embedding))
                                )
                                db.session.add(vektor_add)
                                additional_vectors_count += 1
                            else:
                                failed_images += 1
                        else:
                            failed_images += 1
                    except Exception as e:
                        print(f"Error processing additional image {idx}: {str(e)}")
                        failed_images += 1
                        continue
            
            # Commit semua perubahan
            db.session.commit()
            
            total_vectors = 1 + additional_vectors_count
            total_images = 1 + len(additional_images)
            success_rate = (total_vectors / total_images * 100) if total_images > 0 else 100
            
            if failed_images > 0:
                message = f'Anggota {nama} berhasil ditambahkan! {total_vectors}/{total_images} gambar berhasil diproses.'
            else:
                message = f'Anggota {nama} berhasil ditambahkan dengan {total_vectors} vektor wajah!'
            
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'id_anggota': id_anggota,
                    'nama': nama,
                    'divisi': divisi,
                    'total_vectors': total_vectors,
                    'failed_images': failed_images,
                    'success_rate': f'{success_rate:.1f}%'
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/face/update/<id_anggota>', methods=['PUT'])
    def update_face(id_anggota):
        """
        Update vektor wajah anggota yang sudah ada
        
        Request Body (JSON):
        {
            "images": ["base64_image1", "base64_image2", ...] // Array of base64 images (max 20)
        }
        
        Response:
        {
            "success": true/false,
            "message": "...",
            "data": {...}
        }
        """
        try:
            # Parse request body
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            images = data.get('images', [])
            
            if not images or len(images) == 0:
                return jsonify({
                    'success': False,
                    'message': 'Images harus disertakan!'
                }), 400
            
            # Limit max 20 images
            if len(images) > 20:
                return jsonify({
                    'success': False,
                    'message': 'Maximum 20 images!'
                }), 400
            
            # Cek apakah anggota ada
            anggota = Anggota.query.get(id_anggota)
            if not anggota:
                return jsonify({
                    'success': False,
                    'message': f'Anggota dengan ID "{id_anggota}" tidak ditemukan!'
                }), 404
            
            # Hapus semua vektor lama
            VektorWajah.query.filter_by(id_anggota=id_anggota).delete()
            
            # Process semua gambar dan extract embeddings
            vectors_data = []
            failed_count = 0
            
            for idx, img_base64 in enumerate(images):
                try:
                    # Decode image
                    img = face_service.decode_base64_image(img_base64)
                    if img is None:
                        failed_count += 1
                        continue
                    
                    # Extract embedding
                    embedding = face_service.extract_embedding(img)
                    if embedding is not None:
                        vectors_data.append(embedding)
                    else:
                        failed_count += 1
                        
                except Exception as e:
                    print(f"Error processing image {idx}: {str(e)}")
                    failed_count += 1
                    continue
            
            # Cek apakah ada vektor yang berhasil diextract
            if len(vectors_data) == 0:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Tidak ada wajah yang terdeteksi pada semua gambar!'
                }), 400
            
            # Simpan semua vektor baru ke database
            for vector in vectors_data:
                vw = VektorWajah(
                    id_anggota=id_anggota,
                    vektor=list(map(float, vector))
                )
                db.session.add(vw)
            
            # Update path_wajah dengan gambar pertama yang berhasil
            if vectors_data:
                # Simpan gambar pertama sebagai foto profil
                first_img = face_service.decode_base64_image(images[0])
                if first_img is not None:
                    folder = os.path.join(app.config['UPLOAD_FOLDER'], f"{id_anggota}_{anggota.nama}")
                    os.makedirs(folder, exist_ok=True)
                    
                    timestamp = pd.Timestamp.now().strftime('%Y%m%d%H%M%S')
                    filename = f"updated_{timestamp}.jpg"
                    filepath = os.path.join(folder, filename)
                    
                    face_service.save_image(first_img, filepath)
                    rel_path = os.path.relpath(filepath, app.config['UPLOAD_FOLDER']).replace('\\', '/')
                    anggota.path_wajah = rel_path
            
            # Commit semua perubahan
            db.session.commit()
            
            success_count = len(vectors_data)
            total_images = len(images)
            
            message = f'Vektor wajah {anggota.nama} berhasil diupdate! '
            message += f'{success_count}/{total_images} gambar berhasil diproses.'
            
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'id_anggota': id_anggota,
                    'nama': anggota.nama,
                    'divisi': anggota.divisi,
                    'total_vectors': success_count,
                    'failed_images': failed_count,
                    'success_rate': f'{(success_count/total_images)*100:.1f}%'
                }
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/piket/mulai', methods=['POST'])
    @require_auth
    def mulai_piket():
        """
        Mulai piket dengan real-time face recognition
        
        Headers:
            Authorization: Bearer <token>
        
        Request Body (JSON):
        {
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true,
            "message": "Piket dimulai!",
            "data": {
                "id": "uuid",
                "id_anggota": "...",
                "nama": "...",
                "tanggal": "2025-11-04",
                "jam_masuk": "08:30:00",
                "similarity": 0.95
            }
        }
        """
        try:
            # Get logged in user from token
            id_anggota_login = request.current_user
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            # Get image
            image_base64 = data.get('image', '').strip()
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image wajib diisi'
                }), 400
            
            # Decode image
            try:
                img = face_service.decode_base64_image(image_base64)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid image format: {str(e)}'
                }), 400
            
            # Extract embedding
            try:
                embedding = face_service.extract_embedding(img)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Wajah tidak terdeteksi: {str(e)}'
                }), 400
            
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak terdeteksi. Pastikan wajah terlihat jelas.'
                }), 400
            
            # Find best match from database
            result = face_service.find_best_match_from_db(embedding, db.session)
            
            if not result:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenali!'
                }), 400
            
            # Validasi: wajah harus sesuai dengan user login
            if result['id_anggota'] != id_anggota_login:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak sesuai dengan akun login!'
                }), 403
            
            # Get anggota data
            anggota = Anggota.query.get(id_anggota_login)
            if not anggota:
                return jsonify({
                    'success': False,
                    'message': 'Data anggota tidak ditemukan!'
                }), 404
            
            # Cek sudah piket hari ini?
            today = date.today()
            existing = Absensi.query.filter_by(
                id_anggota=id_anggota_login,
                tanggal=today
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': 'Anda sudah memulai piket hari ini!',
                    'data': {
                        'id': existing.id,
                        'jam_masuk': existing.jam_masuk.strftime('%H:%M:%S') if existing.jam_masuk else None
                    }
                }), 400
            
            # Save foto
            foto_filename = f"{id_anggota_login}_{today.strftime('%Y%m%d')}_{datetime.now().strftime('%H%M%S')}.jpg"
            foto_path = os.path.join(app.config['UPLOAD_FOLDER'], foto_filename)
            
            # Save image to disk
            import cv2
            cv2.imwrite(foto_path, img)
            
            # Insert absensi
            absensi = Absensi(
                id=str(uuid.uuid4()),
                id_anggota=id_anggota_login,
                tanggal=today,
                jam_masuk=datetime.now().time(),
                foto=foto_filename,
                jadwal_piket=None,
                periode_piket=None
            )
            db.session.add(absensi)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Piket dimulai! Selamat bekerja, {anggota.nama}',
                'data': {
                    'id': absensi.id,
                    'id_anggota': absensi.id_anggota,
                    'nama': anggota.nama,
                    'divisi': anggota.divisi,
                    'tanggal': absensi.tanggal.isoformat(),
                    'jam_masuk': absensi.jam_masuk.strftime('%H:%M:%S'),
                    'similarity': result['similarity']
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/piket/akhiri', methods=['POST'])
    @require_auth
    def akhiri_piket():
        """
        Akhiri piket dengan kegiatan dan face recognition
        
        Headers:
            Authorization: Bearer <token>
        
        Request Body (JSON):
        {
            "kegiatan": "Deskripsi kegiatan...",
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true,
            "message": "Piket selesai!",
            "data": {
                "id": "uuid",
                "jam_masuk": "08:30:00",
                "jam_keluar": "16:00:00",
                "durasi": "7 jam 30 menit",
                "kegiatan": "..."
            }
        }
        """
        try:
            # Get logged in user from token
            id_anggota_login = request.current_user
            
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            # Get kegiatan
            kegiatan = data.get('kegiatan', '').strip()
            
            if not kegiatan:
                return jsonify({
                    'success': False,
                    'message': 'Kegiatan harus diisi!'
                }), 400
            
            # Get image
            image_base64 = data.get('image', '').strip()
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image wajib diisi'
                }), 400
            
            # Decode image
            try:
                img = face_service.decode_base64_image(image_base64)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Invalid image format: {str(e)}'
                }), 400
            
            # Extract embedding
            try:
                embedding = face_service.extract_embedding(img)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Wajah tidak terdeteksi: {str(e)}'
                }), 400
            
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak terdeteksi. Pastikan wajah terlihat jelas.'
                }), 400
            
            # Find best match from database
            result = face_service.find_best_match_from_db(embedding, db.session)
            
            if not result or result['id_anggota'] != id_anggota_login:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak sesuai dengan akun login!'
                }), 403
            
            # Get anggota data
            anggota = Anggota.query.get(id_anggota_login)
            if not anggota:
                return jsonify({
                    'success': False,
                    'message': 'Data anggota tidak ditemukan!'
                }), 404
            
            # Cek piket hari ini
            today = date.today()
            absensi = Absensi.query.filter_by(
                id_anggota=id_anggota_login,
                tanggal=today
            ).first()
            
            if not absensi:
                return jsonify({
                    'success': False,
                    'message': 'Anda belum memulai piket hari ini!'
                }), 400
            
            if absensi.jam_keluar:
                return jsonify({
                    'success': False,
                    'message': 'Piket sudah diakhiri sebelumnya!',
                    'data': {
                        'jam_keluar': absensi.jam_keluar.strftime('%H:%M:%S')
                    }
                }), 400
            
            # Update absensi
            absensi.jam_keluar = datetime.now().time()
            absensi.kegiatan = kegiatan
            db.session.commit()
            
            # Get data with duration
            absensi_data = absensi.to_dict()
            absensi_data['nama'] = anggota.nama
            absensi_data['divisi'] = anggota.divisi
            absensi_data['similarity'] = result['similarity']
            
            return jsonify({
                'success': True,
                'message': f'Piket selesai! Terima kasih, {anggota.nama}',
                'data': absensi_data
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/anggota', methods=['GET'])
    def get_anggota():
        """
        Ambil daftar anggota
        
        Query Parameters:
        - id_anggota: Filter by ID (optional)
        - divisi: Filter by divisi (optional)
        
        Response:
        {
            "success": true,
            "data": [...]
        }
        """
        try:
            id_anggota = request.args.get('id_anggota')
            divisi = request.args.get('divisi')
            
            query = Anggota.query
            
            if id_anggota:
                query = query.filter_by(id_anggota=id_anggota)
            
            if divisi:
                query = query.filter_by(divisi=divisi)
            
            anggota_list = query.all()
            
            return jsonify({
                'success': True,
                'data': [a.to_dict() for a in anggota_list],
                'count': len(anggota_list)
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/absensi', methods=['GET'])
    def get_absensi():
        """
        Ambil data absensi
        
        Query Parameters:
        - tanggal: Filter by tanggal (YYYY-MM-DD, optional, default: today)
        - id_anggota: Filter by ID anggota (optional)
        - status: Filter by status (aktif/selesai, optional)
                 aktif = jam_keluar is NULL (belum akhiri piket)
                 selesai = jam_keluar is NOT NULL (sudah akhiri piket)
        
        Response:
        {
            "success": true,
            "data": [...]
        }
        """
        try:
            tanggal_str = request.args.get('tanggal', date.today().isoformat())
            id_anggota = request.args.get('id_anggota')
            status = request.args.get('status')
            
            # Parse tanggal
            try:
                tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Format tanggal harus YYYY-MM-DD'
                }), 400
            
            query = Absensi.query.filter_by(tanggal=tanggal)
            
            if id_anggota:
                query = query.filter_by(id_anggota=id_anggota)
            
            if status:
                if status == 'aktif':
                    # Piket aktif = jam_keluar masih NULL
                    query = query.filter(Absensi.jam_keluar.is_(None))
                elif status == 'selesai':
                    # Piket selesai = jam_keluar sudah terisi
                    query = query.filter(Absensi.jam_keluar.isnot(None))
            
            absensi_list = query.all()
            
            return jsonify({
                'success': True,
                'data': [a.to_dict() for a in absensi_list],
                'count': len(absensi_list),
                'tanggal': tanggal.isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    return app


if __name__ == '__main__':
    # Ambil environment dari environment variable
    env = os.environ.get('FLASK_ENV', 'development')
    app = create_app(env)
    
    # Buat tabel database jika belum ada
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    # Jalankan aplikasi
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=(env == 'development'))

"""
API Pengenalan Wajah untuk Absen Piket Lab
Menggunakan FaceNet untuk face recognition
"""
import os
from datetime import datetime, date, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pandas as pd

from config import config_by_name
from models import db, Anggota, VektorWajah, AbsenPiket
from face_recognition import FaceRecognitionService


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
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'insert_face': '/api/face/insert',
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
            image_base64 = data.get('image', '')
            additional_images = data.get('additional_images', [])
            
            if not id_anggota or not nama or not divisi:
                return jsonify({
                    'success': False,
                    'message': 'id_anggota, nama, dan divisi harus diisi!'
                }), 400
            
            if not image_base64:
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
                    except Exception as e:
                        print(f"Error processing additional image {idx}: {str(e)}")
                        continue
            
            # Commit semua perubahan
            db.session.commit()
            
            total_vectors = 1 + additional_vectors_count
            message = f'Anggota {nama} berhasil ditambahkan dengan {total_vectors} vektor wajah!'
            
            return jsonify({
                'success': True,
                'message': message,
                'data': {
                    'id_anggota': id_anggota,
                    'nama': nama,
                    'divisi': divisi,
                    'total_vectors': total_vectors
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/piket/mulai', methods=['POST'])
    def mulai_piket():
        """
        Mulai piket dengan pengenalan wajah
        
        Request Body (JSON):
        {
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true/false,
            "message": "...",
            "data": {...}
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            image_base64 = data.get('image', '')
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image harus disertakan!'
                }), 400
            
            # Decode gambar
            img = face_service.decode_base64_image(image_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Format gambar tidak valid!'
                }), 400
            
            # Extract embedding
            test_embedding = face_service.extract_embedding(img)
            if test_embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Tidak terdeteksi wajah pada gambar!'
                }), 400
            
            # Ambil semua vektor dari database
            vectors = VektorWajah.query.all()
            if not vectors:
                return jsonify({
                    'success': False,
                    'message': 'Belum ada data wajah terdaftar!'
                }), 404
            
            # Format vektor untuk matching
            stored_embeddings = [(v.id_anggota, v.vektor) for v in vectors]
            
            # Cari kecocokan terbaik
            threshold = app.config['FACE_RECOGNITION_THRESHOLD']
            id_match, score = face_service.find_best_match(
                test_embedding, 
                stored_embeddings, 
                threshold
            )
            
            if not id_match:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenal!',
                    'data': {
                        'confidence': f'{score:.2f}'
                    }
                }), 404
            
            # Ambil data anggota
            anggota = Anggota.query.get(id_match)
            if not anggota:
                return jsonify({
                    'success': False,
                    'message': 'Data anggota tidak ditemukan!'
                }), 404
            
            # Cek apakah sudah mulai piket hari ini
            today = date.today()
            existing = AbsenPiket.query.filter_by(
                id_anggota=id_match,
                tanggal=today,
                jenis='Mulai'
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'{anggota.nama} sudah memulai piket hari ini!',
                    'data': {
                        'id_anggota': anggota.id_anggota,
                        'nama': anggota.nama,
                        'divisi': anggota.divisi,
                        'waktu': existing.waktu.strftime('%H:%M:%S'),
                        'confidence': f'{score:.2f}'
                    }
                }), 400
            
            # Simpan absensi mulai piket
            now = datetime.now().time()
            absen = AbsenPiket(
                id_anggota=id_match,
                tanggal=today,
                waktu=now,
                status='Hadir',
                jenis='Mulai'
            )
            db.session.add(absen)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Selamat datang, {anggota.nama}! Piket dimulai.',
                'data': {
                    'id_anggota': anggota.id_anggota,
                    'nama': anggota.nama,
                    'divisi': anggota.divisi,
                    'tanggal': today.isoformat(),
                    'waktu': now.strftime('%H:%M:%S'),
                    'status': 'Hadir',
                    'jenis': 'Mulai',
                    'confidence': f'{score:.2f}'
                }
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error: {str(e)}'
            }), 500
    
    @app.route('/api/piket/akhiri', methods=['POST'])
    def akhiri_piket():
        """
        Akhiri piket dengan pengenalan wajah
        
        Request Body (JSON):
        {
            "image": "base64_encoded_image"
        }
        
        Response:
        {
            "success": true/false,
            "message": "...",
            "data": {...}
        }
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Request body harus berformat JSON'
                }), 400
            
            image_base64 = data.get('image', '')
            
            if not image_base64:
                return jsonify({
                    'success': False,
                    'message': 'Image harus disertakan!'
                }), 400
            
            # Decode gambar
            img = face_service.decode_base64_image(image_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Format gambar tidak valid!'
                }), 400
            
            # Extract embedding
            test_embedding = face_service.extract_embedding(img)
            if test_embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Tidak terdeteksi wajah pada gambar!'
                }), 400
            
            # Ambil semua vektor dari database
            vectors = VektorWajah.query.all()
            if not vectors:
                return jsonify({
                    'success': False,
                    'message': 'Belum ada data wajah terdaftar!'
                }), 404
            
            # Format vektor untuk matching
            stored_embeddings = [(v.id_anggota, v.vektor) for v in vectors]
            
            # Cari kecocokan terbaik
            threshold = app.config['FACE_RECOGNITION_THRESHOLD']
            id_match, score = face_service.find_best_match(
                test_embedding, 
                stored_embeddings, 
                threshold
            )
            
            if not id_match:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenal!',
                    'data': {
                        'confidence': f'{score:.2f}'
                    }
                }), 404
            
            # Ambil data anggota
            anggota = Anggota.query.get(id_match)
            if not anggota:
                return jsonify({
                    'success': False,
                    'message': 'Data anggota tidak ditemukan!'
                }), 404
            
            # Cek apakah sudah mulai piket hari ini
            today = date.today()
            mulai_piket = AbsenPiket.query.filter_by(
                id_anggota=id_match,
                tanggal=today,
                jenis='Mulai'
            ).first()
            
            if not mulai_piket:
                return jsonify({
                    'success': False,
                    'message': f'{anggota.nama} belum memulai piket hari ini!',
                    'data': {
                        'id_anggota': anggota.id_anggota,
                        'nama': anggota.nama,
                        'divisi': anggota.divisi,
                        'confidence': f'{score:.2f}'
                    }
                }), 400
            
            # Cek apakah sudah akhiri piket hari ini
            existing = AbsenPiket.query.filter_by(
                id_anggota=id_match,
                tanggal=today,
                jenis='Akhir'
            ).first()
            
            if existing:
                return jsonify({
                    'success': False,
                    'message': f'{anggota.nama} sudah mengakhiri piket hari ini!',
                    'data': {
                        'id_anggota': anggota.id_anggota,
                        'nama': anggota.nama,
                        'divisi': anggota.divisi,
                        'waktu_mulai': mulai_piket.waktu.strftime('%H:%M:%S'),
                        'waktu_akhir': existing.waktu.strftime('%H:%M:%S'),
                        'confidence': f'{score:.2f}'
                    }
                }), 400
            
            # Simpan absensi akhir piket
            now = datetime.now().time()
            absen = AbsenPiket(
                id_anggota=id_match,
                tanggal=today,
                waktu=now,
                status='Hadir',
                jenis='Akhir'
            )
            db.session.add(absen)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Terima kasih, {anggota.nama}! Piket selesai.',
                'data': {
                    'id_anggota': anggota.id_anggota,
                    'nama': anggota.nama,
                    'divisi': anggota.divisi,
                    'tanggal': today.isoformat(),
                    'waktu_mulai': mulai_piket.waktu.strftime('%H:%M:%S'),
                    'waktu_akhir': now.strftime('%H:%M:%S'),
                    'status': 'Hadir',
                    'jenis': 'Akhir',
                    'confidence': f'{score:.2f}'
                }
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
        - jenis: Filter by jenis (Mulai/Akhir, optional)
        
        Response:
        {
            "success": true,
            "data": [...]
        }
        """
        try:
            tanggal_str = request.args.get('tanggal', date.today().isoformat())
            id_anggota = request.args.get('id_anggota')
            jenis = request.args.get('jenis')
            
            # Parse tanggal
            try:
                tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Format tanggal harus YYYY-MM-DD'
                }), 400
            
            query = AbsenPiket.query.filter_by(tanggal=tanggal)
            
            if id_anggota:
                query = query.filter_by(id_anggota=id_anggota)
            
            if jenis and jenis in ['Mulai', 'Akhir']:
                query = query.filter_by(jenis=jenis)
            
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

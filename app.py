"""
API Piket - Face Recognition & Attendance System
Menggunakan FaceNet untuk face recognition dengan database SILAB
Version: 3.0 (Simplified)
"""
import os
import uuid
import json
from datetime import datetime, date, time
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import config_by_name
from models import db, Users, VektorWajah, Absensi, JadwalPiket, PeriodePiket
from face_recognition import FaceRecognitionService


def create_app(config_name='development'):
    """Factory function untuk membuat Flask app"""
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Initialize face recognition service
    face_service = FaceRecognitionService()
    
    # Create tables
    with app.app_context():
        db.create_all()
        print("Database tables created successfully!")
    
    # =========================================================================
    # ENDPOINT 1: Health Check
    # =========================================================================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint untuk mengecek status API dan database
        
        Returns:
            JSON response dengan status API
        """
        try:
            # Test database connection
            db.session.execute(db.text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'ok',
            'message': 'API Piket is running',
            'database': db_status,
            'timestamp': datetime.now().isoformat(),
            'version': '3.0'
        }), 200
    
    # =========================================================================
    # ENDPOINT 2: Insert Vektor Wajah dari Kamera (Multiple Images)
    # =========================================================================
    
    @app.route('/api/face/insert', methods=['POST'])
    def insert_face_vectors():
        """
        Insert vektor wajah user dengan multiple images dari streaming kamera
        
        Request Body:
            {
                "user_id": "uuid-string",
                "images": ["base64_image1", "base64_image2", ...] // max 20 images
            }
        
        Returns:
            JSON response dengan status dan data yang tersimpan
        """
        try:
            data = request.get_json()
            
            # Validasi input
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            user_id = data.get('user_id')
            images = data.get('images', [])
            
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'user_id is required'
                }), 400
            
            if not images or len(images) == 0:
                return jsonify({
                    'success': False,
                    'message': 'At least 1 image is required'
                }), 400
            
            if len(images) > 20:
                return jsonify({
                    'success': False,
                    'message': 'Maximum 20 images allowed'
                }), 400
            
            # Cek apakah user ada di database
            user = Users.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User with id {user_id} not found'
                }), 404
            
            # Cek apakah user sudah memiliki vektor wajah
            existing_vectors = VektorWajah.query.filter_by(user_id=user_id).all()
            if existing_vectors:
                return jsonify({
                    'success': False,
                    'message': f'User {user.name} already has face vectors. Use update endpoint instead.',
                    'existing_vectors_count': len(existing_vectors)
                }), 409
            
            # Process setiap gambar dan extract embedding
            embeddings_saved = 0
            errors = []
            
            for idx, img_base64 in enumerate(images, 1):
                try:
                    # Decode base64 image
                    img = face_service.decode_base64_image(img_base64)
                    if img is None:
                        errors.append(f"Image {idx}: Failed to decode")
                        continue
                    
                    # Extract embedding
                    embedding = face_service.extract_embedding(img)
                    if embedding is None:
                        errors.append(f"Image {idx}: No face detected")
                        continue
                    
                    # Simpan vektor ke database
                    vektor_wajah = VektorWajah(
                        user_id=user_id,
                        vektor=embedding.tolist()  # Convert numpy array to list for JSON
                    )
                    db.session.add(vektor_wajah)
                    embeddings_saved += 1
                    
                    print(f"✓ Image {idx}/{len(images)}: Embedding saved")
                    
                except Exception as e:
                    errors.append(f"Image {idx}: {str(e)}")
                    print(f"✗ Image {idx}/{len(images)}: Error - {str(e)}")
            
            # Commit ke database
            if embeddings_saved > 0:
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully saved {embeddings_saved} face vectors for {user.name}',
                    'data': {
                        'user_id': user_id,
                        'name': user.name,
                        'total_images_processed': len(images),
                        'embeddings_saved': embeddings_saved,
                        'errors': errors if errors else None
                    }
                }), 201
            else:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Failed to extract any valid face embeddings',
                    'errors': errors
                }), 400
                
        except Exception as e:
            db.session.rollback()
            print(f"Error in insert_face_vectors: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    # =========================================================================
    # ENDPOINT 3: Update Vektor Wajah User
    # =========================================================================
    
    @app.route('/api/face/update/<user_id>', methods=['PUT'])
    def update_face_vectors(user_id):
        """
        Update vektor wajah user dengan multiple images baru dari streaming kamera
        
        URL Parameter:
            user_id: UUID dari user
        
        Request Body:
            {
                "images": ["base64_image1", "base64_image2", ...] // max 20 images
            }
        
        Returns:
            JSON response dengan status update
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            images = data.get('images', [])
            
            if not images or len(images) == 0:
                return jsonify({
                    'success': False,
                    'message': 'At least 1 image is required'
                }), 400
            
            if len(images) > 20:
                return jsonify({
                    'success': False,
                    'message': 'Maximum 20 images allowed'
                }), 400
            
            # Cek apakah user ada
            user = Users.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User with id {user_id} not found'
                }), 404
            
            # Hapus vektor wajah lama
            old_vectors = VektorWajah.query.filter_by(user_id=user_id).all()
            old_count = len(old_vectors)
            
            for vektor in old_vectors:
                db.session.delete(vektor)
            
            print(f"Deleted {old_count} old face vectors for user {user.name}")
            
            # Process gambar baru dan extract embedding
            embeddings_saved = 0
            errors = []
            
            for idx, img_base64 in enumerate(images, 1):
                try:
                    # Decode base64 image
                    img = face_service.decode_base64_image(img_base64)
                    if img is None:
                        errors.append(f"Image {idx}: Failed to decode")
                        continue
                    
                    # Extract embedding
                    embedding = face_service.extract_embedding(img)
                    if embedding is None:
                        errors.append(f"Image {idx}: No face detected")
                        continue
                    
                    # Simpan vektor baru ke database
                    vektor_wajah = VektorWajah(
                        user_id=user_id,
                        vektor=embedding.tolist()
                    )
                    db.session.add(vektor_wajah)
                    embeddings_saved += 1
                    
                    print(f"✓ Image {idx}/{len(images)}: New embedding saved")
                    
                except Exception as e:
                    errors.append(f"Image {idx}: {str(e)}")
                    print(f"✗ Image {idx}/{len(images)}: Error - {str(e)}")
            
            # Commit ke database
            if embeddings_saved > 0:
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully updated face vectors for {user.name}',
                    'data': {
                        'user_id': user_id,
                        'name': user.name,
                        'old_vectors_count': old_count,
                        'new_vectors_count': embeddings_saved,
                        'total_images_processed': len(images),
                        'errors': errors if errors else None
                    }
                }), 200
            else:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': 'Failed to extract any valid face embeddings',
                    'errors': errors
                }), 400
                
        except Exception as e:
            db.session.rollback()
            print(f"Error in update_face_vectors: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    # =========================================================================
    # ENDPOINT 4: Mulai Piket (Real-time Face Recognition)
    # =========================================================================
    
    @app.route('/api/piket/mulai', methods=['POST'])
    def mulai_piket():
        """
        Mulai piket dengan face recognition (1 foto)
        
        Request Body:
            {
                "image": "base64_image_string"
            }
        
        Returns:
            JSON response dengan data absensi yang dibuat
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Tidak ada data yang disediakan.'
                }), 400
            
            img_base64 = data.get('image')
            
            if not img_base64:
                return jsonify({
                    'success': False,
                    'message': 'Gambar diperlukan'
                }), 400
            
            # Decode image
            img = face_service.decode_base64_image(img_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Gagal mendekode gambar'
                }), 400
            
            # Extract embedding
            embedding = face_service.extract_embedding(img)
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Tidak ada wajah terdeteksi dalam gambar'
                }), 400
            
            # Cari match dari database
            match_result = face_service.find_best_match_from_db(
                embedding, 
                db.session, 
                threshold=float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
            )
            
            if not match_result:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenali. Silakan daftar terlebih dahulu.'
                }), 404
            
            user_id = match_result['user_id']
            user_name = match_result['name']
            similarity = match_result['similarity']
            
            # Get jadwal piket user - WAJIB ada
            jadwal_piket = JadwalPiket.query.filter_by(user_id=user_id).first()
            if not jadwal_piket:
                return jsonify({
                    'success': False,
                    'message': f'{user_name} tidak memiliki jadwal piket'
                }), 400
            
            # Cek apakah user sudah mulai piket hari ini
            today = date.today()
            existing_absensi = Absensi.query.filter_by(
                jadwal_piket=jadwal_piket.id,
                tanggal=today
            ).first()
            
            if existing_absensi and existing_absensi.jam_masuk:
                return jsonify({
                    'success': False,
                    'message': f'{user_name} sudah mulai piket hari ini',
                    'data': existing_absensi.to_dict()
                }), 409
            
            # Get periode piket aktif
            periode_aktif = PeriodePiket.query.filter_by(isactive=True).first()
            if not periode_aktif:
                return jsonify({
                    'success': False,
                    'message': 'Tidak ada periode piket aktif'
                }), 400
            
            # Buat record absensi baru
            absensi_id = str(uuid.uuid4())
            absensi = Absensi(
                id=absensi_id,
                tanggal=today,
                jam_masuk=datetime.now().time(),
                foto='',
                jadwal_piket=jadwal_piket.id,
                kegiatan='',
                periode_piket_id=periode_aktif.id
            )
            
            db.session.add(absensi)
            db.session.commit()
            
            result = absensi.to_dict()
            result['similarity'] = similarity
            
            return jsonify({
                'success': True,
                'message': f'Piket dimulai untuk {user_name}',
                'data': result
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in mulai_piket: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    # =========================================================================
    # ENDPOINT 5: Akhiri Piket (Face Verification + Input Kegiatan)
    # =========================================================================
    
    @app.route('/api/piket/akhiri', methods=['POST'])
    def akhiri_piket():
        """
        Akhiri piket dengan face verification dan input kegiatan (1 foto)
        
        Request Body:
            {
                "image": "base64_image_string",
                "kegiatan": "Deskripsi kegiatan selama piket"
            }
        
        Returns:
            JSON response dengan data absensi yang diupdate
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Data tidak disediakan'
                }), 400
            
            img_base64 = data.get('image')
            kegiatan = data.get('kegiatan', '').strip()
            
            if not img_base64:
                return jsonify({
                    'success': False,
                    'message': 'Gambar diperlukan'
                }), 400
            
            if not kegiatan:
                return jsonify({
                    'success': False,
                    'message': 'kegiatan is required'
                }), 400
            
            # Decode image
            img = face_service.decode_base64_image(img_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Gagal mendekode gambar'
                }), 400
            
            # Extract embedding
            embedding = face_service.extract_embedding(img)
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'Tidak ada wajah terdeteksi dalam gambar'
                }), 400
            
            # Cari match dari database
            match_result = face_service.find_best_match_from_db(
                embedding, 
                db.session, 
                threshold=float(os.getenv('SIMILARITY_THRESHOLD', 0.7))
            )
            
            if not match_result:
                return jsonify({
                    'success': False,
                    'message': 'Wajah tidak dikenali. Silakan coba lagi.'
                }), 404
            
            user_id = match_result['user_id']
            user_name = match_result['name']
            similarity = match_result['similarity']
            
            # Get jadwal piket user
            jadwal_piket = JadwalPiket.query.filter_by(user_id=user_id).first()
            if not jadwal_piket:
                return jsonify({
                    'success': False,
                    'message': f'{user_name} tidak memiliki jadwal piket'
                }), 400
            
            # Cek apakah user sudah mulai piket hari ini
            today = date.today()
            absensi = Absensi.query.filter_by(
                jadwal_piket=jadwal_piket.id,
                tanggal=today
            ).first()
            
            if not absensi:
                return jsonify({
                    'success': False,
                    'message': f'{user_name} belum mulai piket hari ini'
                }), 400
            
            if absensi.jam_keluar:
                return jsonify({
                    'success': False,
                    'message': f'{user_name} sudah mengakhiri piket hari ini',
                    'data': absensi.to_dict()
                }), 409
            
            # Update absensi dengan jam keluar dan kegiatan
            absensi.jam_keluar = datetime.now().time()
            absensi.kegiatan = kegiatan
            
            db.session.commit()
            
            result = absensi.to_dict()
            result['similarity'] = similarity
            
            return jsonify({
                'success': True,
                'message': f'Piket selesai untuk {user_name}',
                'data': result
            }), 200
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in akhiri_piket: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    # =========================================================================
    # ENDPOINT 6: Insert Vektor Wajah dari Upload Foto (Single Image)
    # =========================================================================
    
    @app.route('/api/face/insert-from-photo', methods=['POST'])
    def insert_face_from_photo():
        """
        Buat dan tambah 1 vektor wajah dari upload foto (bukan streaming kamera)
        
        Request Body:
            {
                "user_id": "uuid-string",
                "image": "base64_image_string"
            }
        
        Returns:
            JSON response dengan status dan data yang tersimpan
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'No data provided'
                }), 400
            
            user_id = data.get('user_id')
            img_base64 = data.get('image')
            
            if not user_id:
                return jsonify({
                    'success': False,
                    'message': 'user_id is required'
                }), 400
            
            if not img_base64:
                return jsonify({
                    'success': False,
                    'message': 'image is required'
                }), 400
            
            # Cek apakah user ada di database
            user = Users.query.filter_by(id=user_id).first()
            if not user:
                return jsonify({
                    'success': False,
                    'message': f'User with id {user_id} not found'
                }), 404
            
            # Decode image
            img = face_service.decode_base64_image(img_base64)
            if img is None:
                return jsonify({
                    'success': False,
                    'message': 'Failed to decode image'
                }), 400
            
            # Extract embedding
            embedding = face_service.extract_embedding(img)
            if embedding is None:
                return jsonify({
                    'success': False,
                    'message': 'No face detected in image'
                }), 400
            
            # Simpan vektor ke database
            vektor_wajah = VektorWajah(
                user_id=user_id,
                vektor=embedding.tolist()
            )
            db.session.add(vektor_wajah)
            db.session.commit()
            
            # Hitung total vektor yang dimiliki user
            total_vectors = VektorWajah.query.filter_by(user_id=user_id).count()
            
            return jsonify({
                'success': True,
                'message': f'Face vector saved successfully for {user.name}',
                'data': {
                    'user_id': user_id,
                    'name': user.name,
                    'vector_id': vektor_wajah.id_vektor_wajah,
                    'total_vectors': total_vectors
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error in insert_face_from_photo: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return jsonify({
                'success': False,
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    # =========================================================================
    # Error Handlers
    # =========================================================================
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'message': 'Method not allowed'
        }), 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
    
    return app


# =============================================================================
# Main
# =============================================================================

if __name__ == '__main__':
    # Get configuration from environment variable
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=(config_name == 'development')
    )

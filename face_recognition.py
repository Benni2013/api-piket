"""
Modul Face Recognition menggunakan FaceNet
"""
import cv2
import numpy as np
from keras_facenet import FaceNet
from sklearn.metrics.pairwise import cosine_similarity


class FaceRecognitionService:
    """Service untuk face recognition menggunakan FaceNet"""
    
    def __init__(self):
        """Inisialisasi FaceNet embedder"""
        self.embedder = FaceNet()
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def crop_face_oval(self, img):
        """
        Crop wajah dari gambar dengan mask oval
        
        Args:
            img: Image array (BGR format)
            
        Returns:
            Cropped face image atau None jika tidak terdeteksi
        """
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        axes = (int(w * 0.6 / 2), int(h * 0.6667 / 2))
        
        # Buat mask oval
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
        
        # Terapkan mask
        masked_img = cv2.bitwise_and(img, img, mask=mask)
        
        # Deteksi wajah
        gray = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        # Ambil wajah pertama
        x, y, w_box, h_box = faces[0]
        return masked_img[y:y + h_box, x:x + w_box]
    
    def extract_embedding(self, img):
        """
        Extract embedding dari gambar wajah
        
        Args:
            img: Image array (BGR format)
            
        Returns:
            Embedding array (512 dimensions) atau None jika gagal
        """
        face_img = self.crop_face_oval(img)
        if face_img is None:
            return None
        
        try:
            faces = self.embedder.extract(face_img, threshold=0.95)
            return faces[0]['embedding'] if faces else None
        except Exception as e:
            print(f"Error extracting embedding: {str(e)}")
            return None
    
    def decode_base64_image(self, base64_string):
        """
        Decode base64 string menjadi image array
        
        Args:
            base64_string: Base64 encoded image string (dengan atau tanpa header)
            
        Returns:
            Image array (BGR format) atau None jika gagal
        """
        import base64
        
        try:
            # Remove header jika ada
            if ',' in base64_string:
                base64_string = base64_string.split(',', 1)[1]
            
            # Decode base64
            img_bytes = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return img
        except Exception as e:
            print(f"Error decoding base64 image: {str(e)}")
            return None
    
    def find_best_match(self, test_embedding, stored_embeddings, threshold=0.7):
        """
        Cari kecocokan terbaik dari embedding
        
        Args:
            test_embedding: Embedding yang akan dicocokkan
            stored_embeddings: List of tuples (id_anggota, embedding)
            threshold: Threshold similarity (default 0.7)
            
        Returns:
            Tuple (id_anggota, similarity_score) atau (None, 0) jika tidak cocok
        """
        if not stored_embeddings or test_embedding is None:
            return None, 0
        
        best_match = None
        best_score = 0
        
        for id_anggota, stored_embedding in stored_embeddings:
            try:
                # Validasi stored_embedding adalah numpy array dengan ukuran > 0
                if stored_embedding is not None and isinstance(stored_embedding, np.ndarray) and stored_embedding.size > 0:
                    # Hitung cosine similarity
                    similarity = cosine_similarity(
                        [test_embedding], 
                        [stored_embedding]
                    )[0][0]
                    
                    if similarity > best_score:
                        best_score = similarity
                        best_match = id_anggota
            except Exception as e:
                print(f"Error calculating similarity for {id_anggota}: {str(e)}")
                continue
        
        # Return jika score di atas threshold
        if best_score >= threshold:
            return best_match, best_score
        
        return None, best_score
    
    def save_image(self, img, filepath):
        """
        Simpan image ke file
        
        Args:
            img: Image array
            filepath: Path untuk menyimpan file
            
        Returns:
            True jika berhasil, False jika gagal
        """
        try:
            cv2.imwrite(filepath, img)
            return True
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return False
    
    def find_best_match_from_db(self, test_embedding, db_session, threshold=0.7):
        """
        Cari kecocokan terbaik dari embedding dengan data di database
        
        Args:
            test_embedding: Embedding yang akan dicocokkan
            db_session: SQLAlchemy database session
            threshold: Threshold similarity (default 0.7)
            
        Returns:
            Dictionary dengan data anggota dan similarity, atau None jika tidak cocok
            Format: {
                'id_anggota': '...',
                'nama': '...',
                'divisi': '...',
                'similarity': 0.95
            }
        """
        try:
            # Import models di dalam method untuk menghindari circular import
            from models import Anggota, VektorWajah
            
            # Ambil semua vektor wajah dari database
            vektor_list = db_session.query(VektorWajah).all()
            
            if not vektor_list:
                print("No face embeddings found in database")
                return None
            
            # Siapkan stored_embeddings untuk find_best_match
            stored_embeddings = []
            for vektor in vektor_list:
                try:
                    # Pastikan vektor.vektor adalah numpy array
                    if isinstance(vektor.vektor, str):
                        # Jika masih string, convert ke numpy array
                        import json
                        embedding_array = np.array(json.loads(vektor.vektor))
                    else:
                        embedding_array = np.array(vektor.vektor)
                    
                    stored_embeddings.append((vektor.id_anggota, embedding_array))
                    print(f"✓ Loaded embedding for {vektor.id_anggota} (shape: {embedding_array.shape})")
                except Exception as e:
                    print(f"✗ Error processing embedding for {vektor.id_anggota}: {str(e)}")
                    continue
            
            if not stored_embeddings:
                print("No valid embeddings to compare")
                return None
            
            print(f"Total valid embeddings: {len(stored_embeddings)}")
            
            # Gunakan method find_best_match yang sudah ada
            best_id_anggota, similarity = self.find_best_match(
                test_embedding, 
                stored_embeddings, 
                threshold
            )
            
            if not best_id_anggota:
                print(f"No match found (best similarity: {similarity:.3f}, threshold: {threshold})")
                return None
            
            print(f"✓ Best match: {best_id_anggota} (similarity: {similarity:.3f})")
            
            # Ambil data anggota
            anggota = db_session.query(Anggota).filter_by(id_anggota=best_id_anggota).first()
            
            if not anggota:
                print(f"Anggota {best_id_anggota} not found in database")
                return None
            
            return {
                'id_anggota': anggota.id_anggota,
                'nama': anggota.nama,
                'divisi': anggota.divisi,
                'similarity': float(similarity)
            }
            
        except Exception as e:
            print(f"Error in find_best_match_from_db: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

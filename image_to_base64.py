"""
Helper script untuk convert image ke base64
Berguna untuk testing API dengan Postman atau curl
"""
import base64
import sys
from pathlib import Path


def image_to_base64(image_path, include_header=True):
    """
    Convert image file ke base64 string
    
    Args:
        image_path: Path ke file image
        include_header: Include data URI header (default: True)
    
    Returns:
        Base64 string
    """
    try:
        # Read image file
        with open(image_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Encode ke base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        # Tambahkan header jika diminta
        if include_header:
            # Detect image type dari extension
            ext = Path(image_path).suffix.lower()
            mime_type = 'image/jpeg'
            if ext in ['.png']:
                mime_type = 'image/png'
            elif ext in ['.gif']:
                mime_type = 'image/gif'
            
            return f"data:{mime_type};base64,{base64_data}"
        
        return base64_data
    
    except FileNotFoundError:
        print(f"Error: File '{image_path}' tidak ditemukan!")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


def save_to_file(base64_string, output_file='output_base64.txt'):
    """
    Simpan base64 string ke file
    
    Args:
        base64_string: Base64 string yang akan disimpan
        output_file: Nama file output
    """
    try:
        with open(output_file, 'w') as f:
            f.write(base64_string)
        print(f"✅ Base64 string berhasil disimpan ke: {output_file}")
        return True
    except Exception as e:
        print(f"Error menyimpan file: {str(e)}")
        return False


def main():
    """Main function"""
    print("=" * 60)
    print("Image to Base64 Converter")
    print("=" * 60)
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python image_to_base64.py <image_path> [output_file]")
        print("\nContoh:")
        print("  python image_to_base64.py foto.jpg")
        print("  python image_to_base64.py foto.jpg output.txt")
        print("\nAtau jalankan interaktif:")
        
        # Interactive mode
        image_path = input("\nMasukkan path ke file image: ").strip()
        if not image_path:
            print("Error: Path tidak boleh kosong!")
            return
        
        save_option = input("Simpan ke file? (y/n, default=n): ").strip().lower()
        output_file = None
        
        if save_option == 'y':
            output_file = input("Nama file output (default=output_base64.txt): ").strip()
            if not output_file:
                output_file = 'output_base64.txt'
    else:
        image_path = sys.argv[1]
        output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Convert image
    print(f"\n📷 Converting image: {image_path}")
    base64_string = image_to_base64(image_path)
    
    if base64_string:
        print("✅ Conversion berhasil!")
        
        # Show preview (first 100 chars)
        preview = base64_string[:100] + "..." if len(base64_string) > 100 else base64_string
        print(f"\n📝 Preview (100 chars pertama):")
        print(preview)
        
        print(f"\n📊 Stats:")
        print(f"   Total length: {len(base64_string)} characters")
        
        # Save to file if requested
        if output_file:
            save_to_file(base64_string, output_file)
        else:
            copy_option = input("\n💾 Copy ke clipboard? (membutuhkan pyperclip) (y/n): ").strip().lower()
            if copy_option == 'y':
                try:
                    import pyperclip
                    pyperclip.copy(base64_string)
                    print("✅ Base64 string berhasil dicopy ke clipboard!")
                except ImportError:
                    print("❌ pyperclip tidak terinstall. Install dengan: pip install pyperclip")
                    save_option = input("Simpan ke file sebagai gantinya? (y/n): ").strip().lower()
                    if save_option == 'y':
                        save_to_file(base64_string, 'output_base64.txt')
    else:
        print("❌ Conversion gagal!")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()

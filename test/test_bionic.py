import os
import sys
from app.bionic.processors.main_processor import process_file_with_fallback

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_bionic.py <file_path>")
        return
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"Processing file: {file_path}...")
    try:
        output_path, file_type, success = process_file_with_fallback(file_path)
        
        if success and output_path:
            print(f"Successfully processed file to: {output_path}")
            print(f"File type detected: {file_type}")
            # Attempt to copy to current directory for easier inspection
            try:
                current_dir_copy = os.path.join(".", os.path.basename(output_path))
                import shutil
                shutil.copy(output_path, current_dir_copy)
                print(f"Copied output to: {current_dir_copy}")
            except Exception as copy_e:
                print(f"Could not copy output to current directory: {copy_e}")
        else:
            print(f"Failed to process file: {file_path}. Success: {success}, Path: {output_path}")
    except Exception as e:
        print(f"Error during processing: {e}")

if __name__ == "__main__":
    main() 
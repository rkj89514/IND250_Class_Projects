import os
import re
import sys
from pypdf import PdfWriter, PdfReader


def natural_sort_key(s):
    """Generates a key for sorting strings that contain numbers."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', s)]


def get_user_inputs(file_list, folder_path):
    """Handles confirmation, naming, and text conversion choice."""
    abs_path = os.path.abspath(folder_path)
    print(f"\n--- PDF Merger Scan ---")
    print(f"Location: {abs_path}")
    print(f"Files found ({len(file_list)}):")
    
    for i, filename in enumerate(file_list, 1):
        print(f"  [{i}] {filename}")
    
    while True:
        proceed = input("\nProceed with merge? (y/n): ").strip().lower()
        if proceed in ('n', 'no'):
            return False, None, False
        if proceed in ('y', 'yes'):
            break
        print("Invalid input. Please enter 'y' or 'n'.")

    default_name = "merged_result.pdf"
    print(f"\nNaming the output file (Press Enter for '{default_name}')")
    new_name = input("Desired filename: ").strip()
    
    if not new_name:
        new_name = default_name
    if not new_name.lower().endswith(".pdf"):
        new_name += ".pdf"

    txt_choice = input("Also create a .txt version? (y/n): ")
    do_txt = txt_choice.strip().lower() in ('y', 'yes')
        
    return True, new_name, do_txt


def convert_to_txt(files, folder_path, output_name):
    """Extracts text from PDFs and saves to a .txt file in the same folder."""
    txt_filename = os.path.splitext(output_name)[0] + ".txt"
    full_txt_path = os.path.join(folder_path, txt_filename)
    
    try:
        with open(full_txt_path, "w", encoding="utf-8") as txt_file:
            for filename in files:
                file_path = os.path.join(folder_path, filename)
                # Skip the output file itself if it was already created
                if filename == output_name:
                    continue
                
                reader = PdfReader(file_path)
                txt_file.write(f"\n{'='*10} START: {filename} {'='*10}\n")
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        txt_file.write(text + "\n")
                txt_file.write(f"{'='*10} END: {filename} {'='*10}\n")
        print(f"Text version saved to: {full_txt_path}")
    except Exception as e:
        print(f"DEBUG: Text extraction failed - {e}")


def merge_pdfs(target_folder="."):
    """Scans folder, merges PDFs, and saves output to the SAME folder."""
    if not os.path.isdir(target_folder):
        print(f"Error: Folder '{target_folder}' not found.")
        return

    # Filter for PDFs and sort
    files = [f for f in os.listdir(target_folder) if f.endswith('.pdf')]
    files.sort(key=natural_sort_key)

    if not files:
        print(f"No PDF files found in '{target_folder}'.")
        return

    proceed, output_name, do_txt = get_user_inputs(files, target_folder)

    if not proceed:
        print("Operation cancelled.")
        return

    # Define the full path for the output PDF
    output_path = os.path.join(target_folder, output_name)
    
    merger = PdfWriter()
    try:
        print(f"\nStatus: Merging into {target_folder}...")
        for filename in files:
            # Important: Don't merge the output file into itself 
            # if it already exists from a previous run
            if filename == output_name:
                continue
                
            path = os.path.join(target_folder, filename)
            try:
                # Append file to merger
                merger.append(path)
            except Exception as e:
                print(f"Skipping {filename}: Error reading file ({e})")

        with open(output_path, "wb") as output_file:
            merger.write(output_file)
        
        print("\n" + "-" * 30)
        print("SUCCESS")
        print(f"PDF Saved: {output_path}")

        if do_txt:
            convert_to_txt(files, target_folder, output_name)
            
        print("-" * 30)

    except PermissionError:
        print(f"\nERROR: Could not save to '{output_path}'.")
        print("The file is currently open in another program.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        merger.close()


if __name__ == "__main__":
    # Command line usage: python pdfmerger.py [folder_path]
    folder_to_scan = sys.argv[1] if len(sys.argv) > 1 else "."
    merge_pdfs(folder_to_scan)

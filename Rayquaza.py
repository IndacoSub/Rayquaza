import argparse
import os
import subprocess
import shutil
from pathlib import Path
import tempfile
import hashlib
import sys

def explain_usage():
    print("EXTRACT: Rayquaza.py --og ORIGINAL_FILES_FOLDER --mod MODIFIED_FILES_FOLDER --out OUT_XDELTA_FILES_FOLDER")
    print("APPLY: Rayquaza.py --og ORIGINAL_FILES_FOLDER --xdelta XDELTA_FILES_FOLDER --mod TARGET_FOLDER -a\n")

def calculate_md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def extract_patch(original_files_folder, modified_files_folder, out_xdelta_files_folder, use_installer):
    try:
        for modified_file in Path(modified_files_folder).rglob('*'):
            if modified_file.is_file():
                relative_path = modified_file.relative_to(modified_files_folder)
                original_file = Path(original_files_folder) / relative_path
                out_xdelta_file = Path(out_xdelta_files_folder) / (relative_path.as_posix() + ("_patch" if use_installer else "") + ".xdelta")

                if original_file.exists():
                    original_md5 = calculate_md5(original_file)
                    modified_md5 = calculate_md5(modified_file)
                    print(f"Comparing files: {original_file} and {modified_file}")
                    print(f"Original MD5: {original_md5}")
                    print(f"Modified MD5: {modified_md5}")
                    if original_md5 != modified_md5:
                        out_xdelta_file.parent.mkdir(parents=True, exist_ok=True)
                        command = f"xdelta3-3.1.0-x86_64.exe -s \"{original_file}\" \"{modified_file}\" \"{out_xdelta_file}\""
                        print(f"Executing command: {command}")
                        result = subprocess.run(command, shell=True, capture_output=True, text=True)
                        if result.stdout:
                            print(f"Command output: {result.stdout}")
                        if result.stderr:
                            print(f"Command error: {result.stderr}")
                    else:
                        print(f"No changes detected for file: {relative_path}\n")
                else:
                    print(f"Original file not found: {original_file}")
    except Exception as e:
        print(f"Exception: {e}")

def apply_patch(original_files_folder, xdelta_files_folder, target_folder):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        print(f"Temporary directory created at: {temp_dir_path}")
        for xdelta_file in Path(xdelta_files_folder).rglob('*.xdelta'):
            relative_path = xdelta_file.relative_to(xdelta_files_folder)
            original_file = Path(original_files_folder) / relative_path.with_suffix('')
            temp_target_file = temp_dir_path / relative_path.with_suffix('')

            print(f"Processing xdelta file: {xdelta_file}")
            if original_file.exists():
                temp_target_file.parent.mkdir(parents=True, exist_ok=True)
                command = f"xdelta3-3.1.0-x86_64.exe -d -f -s \"{original_file}\" \"{xdelta_file}\" \"{temp_target_file}\""
                print(f"Executing command: {command}")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.stdout:
                    print(f"Command output: {result.stdout}")
                if result.stderr:
                    print(f"Command error: {result.stderr}")
            else:
                print(f"Original file not found: {original_file}")

        # Copy files from temporary directory to target folder
        for temp_file in temp_dir_path.rglob('*'):
            if temp_file.is_file():
                relative_path = temp_file.relative_to(temp_dir_path)
                final_target_file = Path(target_folder) / relative_path
                final_target_file.parent.mkdir(parents=True, exist_ok=True)
                print(f"Copying {temp_file} to {final_target_file}")
                shutil.copy2(temp_file, final_target_file)

def main():
    parser = argparse.ArgumentParser(description="Rayquaza Patch Utility")
    parser.add_argument('--og', required=True, help="Original files folder")
    parser.add_argument('--mod', help="Modified files folder or target folder")
    parser.add_argument('--out', help="Output xdelta files folder")
    parser.add_argument('--xdelta', help="Xdelta files folder")
    parser.add_argument('--a', action='store_true', help="Apply patch")
    parser.add_argument('--installer', action='store_true', help="For V3UPSManager")

    args = parser.parse_args()

    if not Path("xdelta3-3.1.0-x86_64.exe").exists():
        print("XDelta patcher couldn't be found!")
        return 1

    print(f"Arguments received: {args}")

    if args.a:
        if not args.og or not args.mod or not args.xdelta:
            print("Not enough args!")
            explain_usage()
            return 1
        apply_patch(args.og, args.xdelta, args.mod)
    else:
        if not args.og or not args.mod or not args.out:
            print("Not enough args!")
            explain_usage()
            return 1
        extract_patch(args.og, args.mod, args.out, args.installer)

if __name__ == "__main__":
    print(f"Arguments before parsing: {sys.argv}")
    main()


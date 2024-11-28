import os
import zipfile
from traceback import print_exception

import rarfile
import shutil


def delete_non_zip_files(main_folder):
    for root, _, files in os.walk(main_folder):
        if str(os.path.join(main_folder)) == str(os.path.join(root)):
            print("Skipping main folder: ", main_folder)
            continue

        for file in files:
            file_path = os.path.join(root, file)
            if not file.endswith('.zip'):
                os.remove(file_path)
                print(f"Deleted: {file_path}")


def extract_archives_in_folder(main_folder):
    for file in os.listdir(main_folder):
        file_path = os.path.join(main_folder, file)

        # Process only zip and rar files
        if os.path.isfile(file_path):
            try:
                if file.endswith('.zip'):
                    # Create a folder with the same name as the archive (minus the extension)
                    extract_folder = os.path.join(main_folder, os.path.splitext(file)[0]).strip()
                    # Skip extraction if the folder already exists
                    if os.path.exists(extract_folder):
                        print(f"Extraction folder {extract_folder} already exists. Skipping extraction of {file}.")
                        continue
                    os.makedirs(extract_folder, exist_ok=True)
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_folder)
                    print(f"Extracted {file} to {extract_folder}")
                elif file.endswith('.rar'):
                    # Create a folder with the same name as the archive (minus the extension)
                    extract_folder = os.path.join(main_folder, os.path.splitext(file)[0])
                    # Skip extraction if the folder already exists
                    if os.path.exists(extract_folder):
                        print(f"Extraction folder {extract_folder} already exists. Skipping extraction of {file}.")
                        continue
                    os.makedirs(extract_folder, exist_ok=True)
                    with rarfile.RarFile(file_path, 'r') as rar_ref:
                        rar_ref.extractall(extract_folder)
                    print(f"Extracted {file} to {extract_folder}")
            except (zipfile.BadZipFile, rarfile.Error) as e:
                print(f"Failed to open {file}: {e}. Skipping this file.")


def collect_file_endings_in_folder(folder):
    endings = set()
    for root, _, files in os.walk(folder):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext:
                endings.add(ext)
    return sorted(endings)


def delete_files_with_endings(folder, endings_to_delete):
    for root, _, files in os.walk(folder):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext in endings_to_delete:
                os.remove(os.path.join(root, file))
                print(f"Deleted: {os.path.join(root, file)}")


def flatten_folder(folder):
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            source = os.path.join(root, file)
            destination = os.path.join(folder, file)
            if source != destination:
                shutil.move(source, destination)

        for dir_ in dirs:
            os.rmdir(os.path.join(root, dir_))


from concurrent.futures import ThreadPoolExecutor, as_completed


def create_chapter_zip(folder):
    zip_path = os.path.join(folder, "Chapter.zip")

    # Check if Chapter.zip already exists, if so, skip
    if os.path.exists(zip_path):
        print(f"{zip_path} already exists. Skipping creation.")
        return

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_LZMA) as zipf:
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                # Add only non-zip files
                if os.path.isfile(file_path) and not file.endswith('.zip'):
                    zipf.write(file_path, arcname=file)
        print(f"Created {zip_path} with highest compression")
    except Exception as e:
        print(f"Error creating zip for {folder}: {e}")


def process_folders_in_parallel(main_folder):
    # Collect all subdirectories (folders)
    subfolders = [os.path.join(main_folder, item) for item in os.listdir(main_folder) if
                  os.path.isdir(os.path.join(main_folder, item))]

    # Create a ThreadPoolExecutor with 20 threads
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = []

        for folder in subfolders:
            # Submit the folder to the executor for processing
            futures.append(executor.submit(create_chapter_zip, folder))

        # Wait for all futures to complete
        for future in as_completed(futures):
            try:
                future.result()  # This will re-raise any exceptions that occurred during execution
            except Exception as e:
                print_exception(e)


def process_subdirectories(main_folder):
    # Collect file endings in this folder
    endings = collect_file_endings_in_folder(main_folder)
    print(f"Found file endings in {main_folder}: {endings}")

    # Ask the user for file endings to delete (if any)
    if endings:
        endings_to_delete = input(
            f"Enter file endings to delete in {main_folder} (comma-separated), or press Enter to skip: "
        ).split(',')
        endings_to_delete = [e.strip() for e in endings_to_delete if e.strip()]
        delete_files_with_endings(main_folder, endings_to_delete)

    for item in os.listdir(main_folder):
        subfolder = os.path.join(main_folder, item)
        if os.path.isdir(subfolder):
            print(f"Processing folder: {subfolder}")

            # Flatten the folder structure
            flatten_folder(subfolder)

    process_folders_in_parallel(main_folder)


def main():
    main_folder = input("Enter the path to the main folder: ")

    print("Extracting archives into subdirectories...")
    extract_archives_in_folder(main_folder)

    print("Processing subdirectories...")
    process_subdirectories(main_folder)

    print("Deleting all files that are not .zip...")
    delete_non_zip_files(main_folder)

    print("Done!")


if __name__ == "__main__":
    main()

import os
import zipfile
from PIL import Image
from concurrent.futures import ThreadPoolExecutor


# Function to list and sort files numerically
def sorted_zip_contents(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # List files and sort them based on numeric value, handling _sd entries as well
        files = zip_ref.namelist()
        files_sorted = sorted(files,
                              key=lambda f: (int(f.split('_')[0]) if f.split('_')[0].isdigit() else float('inf'), f))
        return files_sorted


# Function to extract the first entry and rename it to "cover"
def extract_and_convert_to_jpg(zip_path, subdir):
    cover_path = os.path.join(subdir, 'cover.jpg')

    # Check if cover.jpg already exists
    if os.path.exists(cover_path):
        print(f"cover.jpg already exists in {subdir}. Skipping this directory.")
        return  # Skip processing this subdirectory

    files_sorted = sorted_zip_contents(zip_path)

    # Extract the first entry
    first_file = files_sorted[0]

    # Extract the file to the subdirectory
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extract(first_file, subdir)

    # Determine the original path of the extracted file
    original_path = os.path.join(subdir, first_file)

    # Renaming the file to 'cover' while keeping its extension
    file_extension = os.path.splitext(first_file)[1]
    new_path = os.path.join(subdir, 'cover' + file_extension)
    os.rename(original_path, new_path)

    # Convert the file to JPG if it's not already a JPG
    if file_extension.lower() not in ['.jpg', '.jpeg']:
        try:
            with Image.open(new_path) as img:
                # Convert to RGB if it's not already in that mode
                img = img.convert('RGB')
                # Save as JPG
                jpg_path = os.path.join(subdir, 'cover.jpg')
                img.save(jpg_path, 'JPEG')
                # Remove the original file if it was converted to JPG
                os.remove(new_path)
                print(f"Converted and saved as {jpg_path}")
        except Exception as e:
            print(f"Error converting image {new_path}: {e}")
    else:
        print(f"File {new_path} is already in JPG format.")

    # Create empty .nomedia and .noxml files
    nomedia_path = os.path.join(subdir, '.nomedia')
    noxml_path = os.path.join(subdir, '.noxml')

    # Create empty .nomedia file
    with open(nomedia_path, 'w') as f:
        pass  # Creates an empty file

    # Create empty .noxml file
    with open(noxml_path, 'w') as f:
        pass  # Creates an empty file

    print(f"Added .nomedia and .noxml to {subdir}")


# Function to process a single subdirectory
def process_subdir(subdir):
    for file in os.listdir(subdir):
        if file == 'Chapter.zip':
            zip_path = os.path.join(subdir, file)
            extract_and_convert_to_jpg(zip_path, subdir)
            print(f"Processed: {zip_path}")


# Ask the user for the parent directory path
parent_directory = input("Enter the path to the parent folder: ").strip()

# Ensure the path exists
if not os.path.isdir(parent_directory):
    print("Invalid directory path. Please check the path and try again.")
else:
    # Collect all subdirectories to process
    subdirs_to_process = [os.path.join(parent_directory, subdir) for subdir in os.listdir(parent_directory) if
                          os.path.isdir(os.path.join(parent_directory, subdir))]

    # Use ThreadPoolExecutor to process up to 20 subdirectories in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Map the subdirectories to the processing function
        executor.map(process_subdir, subdirs_to_process)

    print("All tasks completed.")

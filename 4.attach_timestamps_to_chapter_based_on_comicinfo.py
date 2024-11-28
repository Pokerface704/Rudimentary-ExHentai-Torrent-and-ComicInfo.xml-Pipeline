import os
import xml.etree.ElementTree as ET
import time
import platform
from datetime import datetime


# Function to update timestamps for all files in a folder
def update_timestamps(main_folder):
    for manga_name in os.listdir(main_folder):
        manga_folder = os.path.join(main_folder, manga_name)
        if not os.path.isdir(manga_folder):
            continue

        comicinfo_path = os.path.join(manga_folder, "ComicInfo.xml")

        # Skip if ComicInfo.xml does not exist
        if not os.path.exists(comicinfo_path):
            print(f"Skipping '{manga_name}' as ComicInfo.xml is missing.")
            continue

        try:
            # Parse ComicInfo.xml to extract year, month, and day
            tree = ET.parse(comicinfo_path)
            root = tree.getroot()
            year = int(root.find("Year").text)
            month = int(root.find("Month").text)
            day = int(root.find("Day").text)
        except Exception as e:
            print(f"Error parsing ComicInfo.xml for '{manga_name}': {e}")
            continue

        # Convert date to timestamp
        dt = datetime(year, month, day)
        timestamp = time.mktime(dt.timetuple())

        # Update timestamps for all files in the folder
        try:
            for file_name in os.listdir(manga_folder):
                file_path = os.path.join(manga_folder, file_name)

                if os.path.isfile(file_path):
                    os.utime(file_path, (timestamp, timestamp))

            print(f"Timestamps updated for all files in '{manga_folder}' to {dt.strftime('%Y-%m-%d')}")

            # Update the folder's timestamp
            if platform.system() == "Windows":
                os.utime(manga_folder, (timestamp, timestamp))

        except Exception as e:
            print(f"Error updating timestamps for files in '{manga_folder}': {e}")


if __name__ == "__main__":
    main_folder_global = input("Enter the path to the main folder: ").strip()
    update_timestamps(main_folder_global)

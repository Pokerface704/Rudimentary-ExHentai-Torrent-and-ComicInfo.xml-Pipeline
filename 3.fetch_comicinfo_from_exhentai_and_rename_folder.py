import os
import re
import urllib.parse
import webbrowser
from datetime import datetime
from traceback import print_exception
from xml.dom import minidom

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Function to fetch metadata from ExHentai
def fetch_metadata(manga_name, cookies):
    url_enc = urllib.parse.quote(manga_name)
    search_url = f"https://exhentai.org/?f_search=\"{url_enc}\""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(search_url, headers=headers, cookies=cookies)
    if response.status_code != 200:
        print(f"Failed to fetch metadata for '{manga_name}'. HTTP Status: {response.status_code}")
        return None

    print("General search: ", search_url)

    # Parse search results with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')
    gallery = soup.find('table', class_='glte')
    if not gallery:
        print(f"#1 No results found for '{manga_name}' on ExHentai.")
        webbrowser.open(search_url)
        return None

    # Extract title, link, and tags

    child = gallery.find_all_next("tr")

    if not child:
        print(f"#2 No results found for '{manga_name}' on ExHentai.")
        webbrowser.open(search_url)
        return None

    try:
        gallery_url = child[0].find("td", class_="gl1e").find_next("a")["href"]

        if not gallery_url:
            return None

        return fetch_metadata_gallery(gallery_url, cookies)
    except Exception as e:
        print_exception(e)
        return None


def fetch_metadata_gallery(gallery_url, cookies, parse_parent=True):
    print("Gallery search: ", gallery_url)

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(gallery_url, headers=headers, cookies=cookies)
    if response.status_code != 200:
        print(f"Failed to fetch metadata for '{gallery_url}'. HTTP Status: {response.status_code}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')

    title_info = soup.find('div', id='gd2')
    title_info = [x.text for x in title_info.find_all("h1")]

    posted_info = soup.find('td', class_='gdt1', string='Posted:').find_next_sibling('td', class_='gdt2').text
    parsed_info = datetime.strptime(posted_info, "%Y-%m-%d %H:%M")

    # Extract year, month, and day as strings with leading zeros
    year = f"{parsed_info.year:04d}"  # Ensures 4 digits for year
    month = f"{parsed_info.month:02d}"  # Ensures 2 digits for month
    day = f"{parsed_info.day:02d}"  # Ensures 2 digits for day

    genre_info = soup.find('div', id='gd3').find("div", id="gdc").text

    tag_info = soup.find("div", id="taglist").find_all("tr")
    tags = []

    publisher_info = soup.find("div", id="gd3").find("div", id="gdn").text

    # Loop through each row
    for tag_row in tag_info:
        # Find all <td> elements in the row
        td_elements = tag_row.find_all('td')

        # Skip rows that don't have a second <td>
        if len(td_elements) > 1:
            # Get the second <td>
            second_td = td_elements[1]

            # Find all <div> elements inside the second <td>
            divs = second_td.find_all('div')

            # Extract and append the text from each <div> to the all_contents list
            tags.extend([div.text for div in divs])

    page_count_info = \
        soup.find('td', class_='gdt1', string='Length:').find_next_sibling('td', class_='gdt2').text.split(" ")[0]

    summary_info = ""

    summary_info += f"Title: \t{title_info[0]}\r\n"

    if len(title_info) > 1:
        summary_info += f"\r\nAlternate Title: \t{title_info[1]}"

    summary_info += "\r\n\r\n"

    summary_info += f"Web: {gallery_url}\r\n\r\n"

    summary_info += f"Category: \t{soup.find('div', id='gdc').text}\r\n"
    summary_info += f"Publisher: \t{soup.find('div', id='gdn').text}"

    summary_info += "\r\n\r\n"

    for tr_info in soup.find('div', id='gdd').find_all("tr"):
        tr_name = tr_info.find("td", class_="gdt1").text
        tr_content = tr_info.find("td", class_="gdt2").text

        if "Parent:" in tr_name:
            for tr_link in tr_info.find("td", class_="gdt2").find_all("a"):
                tr_content += f" ({tr_link['href']})"

        summary_info += f'{tr_name} \t{tr_content}\r\n'

    summary_info += "\r\n"

    summary_info += "Tags: \r\n"

    for tag_info in soup.find('div', id='taglist').find_all("tr"):
        td_tags = tag_info.find_all("td")

        summary_info += f'{td_tags[0].text} \t{", ".join([x.text for x in td_tags[1].children])}\r\n'

    summary_info += "\r\n"
    summary_info += f"Rating: {soup.find(id='rating_label').text} / 5 @ {soup.find(id='rating_count').text}"

    for comment_info in soup.find_all('div', id='comment_0'):
        summary_info += "\r\n\r\n"
        summary_info += f'Publisher\'s comment: \r\n{comment_info.text}'

    res = {
        "Title": title_info[0],
        "Series": title_info[0],
        "LocalizedSeries": title_info[1] if len(title_info) > 1 else title_info[0],
        "Web": gallery_url,
        "AgeRating": "R18+",
        "Year": year,
        "Month": month,
        "Day": day,
        "Genre": genre_info,
        "Tags": ", ".join(tags),
        "Publisher": publisher_info,
        "PageCount": page_count_info,
        "Number": str(1),
        "Writer": publisher_info,
        "Penciller": publisher_info,
        "Inker": publisher_info,
        "Colorist": publisher_info,
        "Letterer": publisher_info,
        "CoverArtist": publisher_info,
        "Editor": publisher_info,
        "Imprint": "ExHentai.org",
        "Summary": summary_info,
    }

    parent_info = soup.find('td', class_='gdt1', string='Parent:').find_next_sibling('td', class_='gdt2')

    if parse_parent and parent_info.text.strip().lower() != "None".lower():
        print("Parent info is: ", parent_info.text)
        res2 = fetch_metadata_gallery(parent_info.find("a")["href"], cookies, False)
        if res2 is not None:
            res["Year"] = res2["Year"]
            res["Day"] = res2["Day"]
            res["Month"] = res2["Month"]
            res["Translator"] = res["Publisher"]
            res["Publisher"] = res2["Publisher"]

    print(res)

    return res


# Function to create ComicInfo.xml
def create_comicinfo_xml(folder, metadata):
    root = ET.Element("ComicInfo", {
        "xmlns:xsd": "http://www.w3.org/2001/XMLSchema",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xmlns:ty": "http://www.w3.org/2001/XMLSchema",  # Add ty namespace
        "xmlns:mh": "http://www.w3.org/2001/XMLSchema"  # Add mh namespace
    })

    for key, value in metadata.items():
        ET.SubElement(root, key).text = value

    # Add the additional tags with namespaces
    ET.SubElement(root, "ty:PublishingStatusTachiyomi").text = "Completed"
    ET.SubElement(root, "mh:SourceMihon").text = "E-Hentai"

    tree = ET.ElementTree(root)
    output_path = os.path.join(folder, "ComicInfo.xml")
    # Convert the tree to a byte string
    xml_str = ET.tostring(root, 'utf-8', xml_declaration=True)

    # Pretty-print the XML using minidom
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")

    # Write the pretty-printed XML to the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)

    print(f"ComicInfo.xml created for '{metadata['Title']}' in {folder}")


def escape_title_to_folder_name(title):
    # Replace any character that is not a letter, digit, or space with a hyphen
    # You can adjust the regex to your specific needs, depending on what is considered illegal.
    folder_name = re.sub(r'[<>:"/\\|?*]', '-', title)  # Replace illegal characters
    folder_name = folder_name.strip()  # Remove leading/trailing spaces
    # folder_name = folder_name.replace(" ", "_")  # Optionally replace spaces with underscores

    # Check if the folder name is valid (e.g., not empty or just hyphens)
    if not folder_name:
        folder_name = "default_folder"

    return folder_name


# Main function to process all manga folders
def process_manga_folder(main_folder, cookies):
    for manga_name in os.listdir(main_folder):
        manga_folder = os.path.join(main_folder, manga_name)
        if not os.path.isdir(manga_folder):
            continue

        # Check if ComicInfo.xml already exists in the folder
        comic_info_path = os.path.join(manga_folder, "ComicInfo.xml")
        if os.path.exists(comic_info_path):
            print(f"Skipping '{manga_name}' because ComicInfo.xml already exists.")
            continue

        print(f"Processing manga: {manga_name}")
        metadata = fetch_metadata(manga_name, cookies)

        if not metadata:
            print("There was a problem fetching metadata for: ", manga_name)
            manual_url = input("Enter gallery url (or leave blank for skip)").strip()

            if len(manual_url) != 0:
                metadata = fetch_metadata_gallery(manual_url, cookies)

        if metadata:
            create_comicinfo_xml(manga_folder, metadata)

            # Check if .noxml exists and delete it
            noxml_path = os.path.join(manga_folder, ".noxml")
            if os.path.exists(noxml_path):
                os.remove(noxml_path)
                print(f"Deleted '.noxml' in '{manga_name}'.")

            # If the manga folder name doesn't match the metadata title, rename it
            metadata_title = escape_title_to_folder_name(metadata['Title'].strip())
            if len(metadata_title) != 0 and manga_name != metadata_title and not os.path.exists(
                    os.path.join(manga_folder, metadata_title)):
                new_folder_name = os.path.join(main_folder, metadata_title)
                os.rename(manga_folder, new_folder_name)
                print(f"Renamed '{manga_name}' to '{metadata_title}'")

        else:
            print(f"Skipping '{manga_name}' due to missing metadata.")


def list_folders_with_one_element(base_path):
    folders_with_one_element = []

    for root, dirs, files in os.walk(base_path):
        # Combine files and dirs to count total elements
        total_elements = len(dirs) + len(files)

        # If the folder itself contains exactly one item
        if total_elements < 3:
            folders_with_one_element.append(root)

    return folders_with_one_element

# Main script execution
if __name__ == "__main__":
    main_folder_global = input("Enter the path to the main folder containing manga subfolders: ").strip()

    # Load cookies from environment variables using dotenv
    cookies_global = {
        "ipb_member_id": os.getenv("IPB_MEMBER_ID"),
        "ipb_pass_hash": os.getenv("IPB_PASS_HASH"),
        "igneous": os.getenv("IGNEOUS"),
        "sk": os.getenv("SK")
    }

    # Check if cookies are properly set
    if not all(cookies_global.values()):
        print(
            "Error: Missing required cookies. Make sure IPB_MEMBER_ID, IPB_PASS_HASH, SK, and IGNEOUS are set in your .env file.")
        exit(1)

    # Process the provided folder
    process_manga_folder(main_folder_global, cookies_global)

    print("Finished ... checking folder contents")

    result = list_folders_with_one_element(main_folder_global)

    # Print folders that contain only one element
    print(f"Folders with less then 3 elements: ({len(result)})")
    for folder in result:
        print(folder)

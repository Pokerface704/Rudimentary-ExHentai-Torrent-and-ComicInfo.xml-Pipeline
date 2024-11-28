# Rudimentary ExHentai Torrent and ComicInfo.xml Pipeline to Comply With Mihon’s Local File Structure
A rudimentary pipeline for extracting a bunch of `.zip`/`.rar` archives (presumably torrents from ExHentai), converting them to [Mihon](https://mihon.app/)'s required local file structure and afterwards (re)attaching metadata to the extracted mangas.

# Warning
This pipeline will extract, delete and modify files in the selected folder. Use a fresh folder with only mangas inside, to minimize the risk of unwanted sideeffects.

**Use at your own risk.**

## Brief summary of individual files
1. Select a folder. All .zip and .rar archives will be extracted into corresponding subdirectories (if already present, skip archive). All files will be flattened (if subdirectories present, their content will be put into the root of the extraction folder). All filetypes will be listed (`.png`, `.jpg`, ...) with the manual option to delete unwanted ones (f. e. `.txt`, `.json`, ...). After that all extracted files will be compressed again to `Chapter.zip` and all files that are not .zip will be deleted from each subdirectory again. After that the empty files `.nomedia` and `.noxml` are added.

2. Select a folder. All subdirectories will be scanned. If `cover.jpg` is not present, the contents of `Chapter.zip` will be numerically sorted and the first entry is fetched. If not .jpg it will be converted. `cover.jpg` will be created.

3. Select a folder. All subdirectories will be scanned. If `ComicInfo.xml` is not present, try searching for the folder name on ExHentai using the credentials set in `.env`. If at least one gallery is found, use the first one as metadata source. If no galleries are found, open a new browser tab with the search on ExHentai and wait for manual input of a gallery url. (Can be skipped if left empty). If metadata is found successfully, rename the folder to the retrieved title (while replacing illegal filename characters with `-`).

4. Select a folder. All subdirectories will be scanned. If `ComicInfo.xml` is present, set the access and modify date of the subdirectory as well as all included files to the retrieved year, month and day in `ComicInfo.xml`.

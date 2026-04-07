from auxFunctions import *
import json
from PIL import Image
import PySimpleGUI as sg

def mainProcess(browserPath, window, editedW):
    piexifCodecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]
    videoCodecs = [k.casefold() for k in ['MP4', 'MOV', '3GP', 'M4V', 'MKV']]

    mediaMoved = {}  # dict to keep track of media moved per directory
    root_fixed = os.path.join(browserPath, "MatchedMedia")
    root_nonEdited = os.path.join(browserPath, "EditedRaw")
    errorCounter = 0
    successCounter = 0
    editedWord = editedW or "editado"
    print(editedWord)

    try:
        json_files = []
        for root, dirs, files in os.walk(browserPath):
            # Prevent os.walk from entering the destination folders
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in (root_fixed, root_nonEdited)]
            
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))
                    
        json_files.sort(key=lambda s: len(os.path.basename(s))) #Sort by length to avoid name(1).jpg be processed before name.jpg
    except Exception as e:
        window.write_event_value('-UPDATE_ERROR-', "Choose a valid directory")
        return

    if not json_files:
        window.write_event_value('-UPDATE_ERROR-', "No JSON files found in this directory")
        return

    total_files = len(json_files)
    for index, json_path in enumerate(json_files):
        try:
            with open(json_path, encoding="utf8") as f:  # Load JSON into a var
                data = json.load(f)
        except Exception as e:
            print(f"[{index + 1}/{total_files}] Error loading JSON {json_path}: {e}")
            errorCounter += 1
            continue

        progress = round((index / total_files) * 100, 2)
        window.write_event_value('-UPDATE_PROGRESS-', progress)

        # Skip system JSONs from Google Takeout that don't belong to media files
        if 'title' not in data or 'photoTakenTime' not in data:
            continue

        titleOriginal = data['title']  # Store metadata into vars
        # clean json name 
        for ext in ['.supplemental-metadata', '.supplemental-metada']:
            titleOriginal: str = titleOriginal.replace(ext, '')

        current_dir = os.path.dirname(json_path)
        rel_dir = os.path.relpath(current_dir, browserPath)
        if rel_dir == ".":
            rel_dir = ""
            
        fixedMediaPath = os.path.join(root_fixed, rel_dir)
        nonEditedMediaPath = os.path.join(root_nonEdited, rel_dir)
        
        os.makedirs(fixedMediaPath, exist_ok=True)
        os.makedirs(nonEditedMediaPath, exist_ok=True)

        # Gestion des suffixes Google Photos cachés (_PORTRAIT, _MFNR, etc.)
        parts = titleOriginal.rsplit('.', 1)
        base_candidates = [titleOriginal]
        if len(parts) == 2:
            # 1. Essayer d'ajouter le suffixe si la photo l'a, mais pas le JSON
            for suffix in ['_PORTRAIT', 'PORTRAIT', '_NFNR', '_MFNR']:
                base_candidates.append(f"{parts[0]}{suffix}.{parts[1]}")
            
            # 2. Essayer de retirer le suffixe si le JSON l'a, mais pas la photo
            for suffix in ['_PORTRAIT', 'PORTRAIT', '_NFNR', '_MFNR']:
                if parts[0].endswith(suffix):
                    base_candidates.append(f"{parts[0][:-len(suffix)]}.{parts[1]}")

        if current_dir not in mediaMoved:
            mediaMoved[current_dir] = []

        title = "None"
        try:
            for candidate_title in base_candidates:
                title = searchMedia(current_dir, candidate_title, mediaMoved[current_dir], nonEditedMediaPath, editedWord)
                if str(title) != "None":
                    titleOriginal = candidate_title
                    break
        except Exception as e:
            print("Error on searchMedia() with file " + titleOriginal)
            errorCounter += 1
            continue

        filepath = None
        already_moved = False
        if str(title) == "None":
            # Fusion : Vérifier si le fichier a déjà été déplacé par un autre JSON
            for candidate_title in base_candidates:
                if os.path.exists(os.path.join(fixedMediaPath, candidate_title)):
                    titleOriginal = candidate_title
                    title = candidate_title
                    filepath = os.path.join(fixedMediaPath, title)
                    already_moved = True
                    break
                else:
                    cand_parts = candidate_title.rsplit('.', 1)
                    if len(cand_parts) == 2:
                        edited_title = f"{cand_parts[0]}-{editedWord}.{cand_parts[1]}"
                        if os.path.exists(os.path.join(fixedMediaPath, edited_title)):
                            titleOriginal = candidate_title
                            title = edited_title
                            filepath = os.path.join(fixedMediaPath, title)
                            already_moved = True
                            break
            
            if not already_moved:
                print(titleOriginal + " not found")
                errorCounter += 1
                continue
        else:
            filepath = os.path.join(current_dir, title)

        # METADATA EDITION
        try:
            timeStamp = int(data['photoTakenTime']['timestamp'])  # Get creation time

            # Extraction sécurisée des coordonnées (évite le crash si absentes du JSON)
            geoData = data.get('geoData', {})
            lat = geoData.get('latitude', 0.0)
            lng = geoData.get('longitude', 0.0)
            alt = geoData.get('altitude', 0.0)
            description = data.get('description', '')

            # Extraction sécurisée de l'extension (évite le crash si pas d'extension)
            parts = title.rsplit('.', 1)
            ext = parts[1].casefold() if len(parts) > 1 else ""

            if ext in piexifCodecs:  # If EXIF is supported
                try:
                    set_EXIF(filepath, lat, lng, alt, timeStamp, description)
                except Exception as e:  # Error handler
                    print("Inexistent EXIF data for " + filepath)
                    print(str(e))
                    errorCounter += 1
                    continue

            elif ext in videoCodecs:  # If it's a video
                try:
                    print(f"Processing video, please wait... ({title})")
                    set_video_metadata(filepath, lat, lng, alt, timeStamp, description)
                except Exception as e:  # Error handler
                    print("Error setting video metadata for " + filepath)
                    print(str(e))
                    errorCounter += 1
                    continue

            setWindowsTime(filepath, timeStamp) #Windows creation and modification time

            #MOVE FILE AND DELETE JSON
            if not already_moved:
                os.replace(filepath, os.path.join(fixedMediaPath, title))
                mediaMoved[current_dir].append(title)
                
            os.remove(json_path)
            successCounter += 1
            print(f"[{index + 1}/{total_files}] Matched successfully: {title}")
            
        except Exception as e:
            print(f"[{index + 1}/{total_files}] Critical error processing {titleOriginal}: {str(e)}")
            errorCounter += 1
            continue

    window.write_event_value('-UPDATE_DONE-', (successCounter, errorCounter))

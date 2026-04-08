import os
import json
import PySimpleGUI as sg
from auxFunctions import *

def mainProcess(browserPath, window, editedW):
    # Supported extensions
    piexifCodecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']] #TODO: PNG ?
    videoCodecs = [k.casefold() for k in ['MP4', 'MOV', '3GP', 'M4V', 'MKV']]

    mediaMoved: dict[str, list[str]] = {}
    root_fixed = os.path.join(browserPath, "MatchedMedia")
    root_nonEdited = os.path.join(browserPath, "EditedRaw")
    
    errorCounter = 0
    successCounter = 0
    editedWord = editedW or "editado"

    try:
        json_files = []
        for root, dirs, files in os.walk(browserPath):
            # Exclude output folders from search
            dirs[:] = [d for d in dirs if os.path.join(root, d) not in (root_fixed, root_nonEdited)]
            file: str = "" 
            for file in files:
                if file.endswith(".json"):
                    json_files.append(os.path.join(root, file))
        
        # Sort by filename length to process originals before duplicates
        json_files.sort(key=lambda s: len(os.path.basename(s)))
    except Exception as e:
        window.write_event_value('-UPDATE_ERROR-', "Invalid directory selected")
        return

    if not json_files:
        window.write_event_value('-UPDATE_ERROR-', "No JSON files found")
        return

    total_files = len(json_files)
    for index, json_path in enumerate(json_files):
        try:
            with open(json_path, encoding="utf8") as f:
                data = json.load(f)
        except Exception:
            errorCounter += 1
            continue

        progress = round(((index + 1) / total_files) * 100, 2)
        window.write_event_value('-UPDATE_PROGRESS-', progress)

        if 'title' not in data or 'photoTakenTime' not in data:
            continue

        titleOriginal:str = data['title']
        # Clean supplemental metadata suffixes
        for ext in ['.supplemental-metadata', '.supplemental-metada']:
            titleOriginal = titleOriginal.replace(ext, '')

        current_dir = os.path.dirname(json_path)
        rel_dir = os.path.relpath(current_dir, browserPath)
        if rel_dir == ".": rel_dir = ""
            
        fixedMediaPath = os.path.join(root_fixed, rel_dir)
        nonEditedMediaPath = os.path.join(root_nonEdited, rel_dir)
        
        os.makedirs(fixedMediaPath, exist_ok=True)
        os.makedirs(nonEditedMediaPath, exist_ok=True)

        # Handle Google Photos hidden suffixes
        parts = titleOriginal.rsplit('.', 1)
        base_candidates = [titleOriginal]
        if len(parts) == 2:
            for suffix in ['_PORTRAIT', 'PORTRAIT', '_NFNR', '_MFNR']:
                base_candidates.append(f"{parts[0]}{suffix}.{parts[1]}")
            for suffix in ['_PORTRAIT', 'PORTRAIT', '_NFNR', '_MFNR']:
                if parts[0].endswith(suffix):
                    base_candidates.append(f"{parts[0][:-len(suffix)]}.{parts[1]}")

        if current_dir not in mediaMoved:
            mediaMoved[current_dir] = []

        title = "None"
        for candidate in base_candidates:
            title = searchMedia(current_dir, candidate, mediaMoved[current_dir], nonEditedMediaPath, editedWord)
            if str(title) != "None":
                titleOriginal = candidate
                break

        filepath = None
        already_moved = False
        
        if str(title) == "None":
            # Check if already moved
            for cand in base_candidates:
                if os.path.exists(os.path.join(fixedMediaPath, cand)):
                    title = cand
                    filepath = os.path.join(fixedMediaPath, title)
                    already_moved = True
                    break
            if not already_moved:
                errorCounter += 1
                continue
        else:
            filepath = os.path.join(current_dir, title)

        
        try:
            # set data to dict for IDE and the method .get 
            data: dict = data 
            
            photo_info: dict = data.get('photoTakenTime', {})
            
            timeStamp = int(photo_info.get('timestamp', 0))
         
            # Location of the photo
            geoData: dict = data.get('geoData', {})
            lat = float(geoData.get('latitude', 0.0))
            lng = float(geoData.get('longitude', 0.0))
            alt = float(geoData.get('altitude', 0.0))
            
            description = data.get('description', '')

            origin = data.get('googlePhotosOrigin', {})
            
            # Check if it if a dict for Type Hinting (more particulary .get)
            if isinstance(origin, dict):
                mobile = origin.get('mobileUpload', {})
                if isinstance(mobile, dict):
                    folder = mobile.get('deviceFolder', {})
                    if isinstance(folder, dict):
                        camera_make = folder.get('localFolderName', '')
                    else:
                        camera_make = ""
                else:
                    camera_make = ""
            else:
                camera_make = ""
           
            camera_model = "" 
            software = "" 

            ext = title.rsplit('.', 1)[1].casefold() if '.' in title else ""


            # Set metadatas
            if ext in piexifCodecs:
                set_photo_metadata(filepath, lat, lng, alt, timeStamp, description)
            elif ext in videoCodecs:
                set_video_metadata(filepath, lat, lng, alt, timeStamp, description, camera_make, camera_model, "", software)

            setWindowsTime(filepath, timeStamp)

            if not already_moved:
                os.replace(filepath, os.path.join(fixedMediaPath, title))
                mediaMoved[current_dir].append(title)
                
            os.remove(json_path)
            successCounter += 1
            
        except Exception as e:
            print(f"Error processing {title}: {e}")
            errorCounter += 1
            continue

    window.write_event_value('-UPDATE_DONE-', (successCounter, errorCounter))
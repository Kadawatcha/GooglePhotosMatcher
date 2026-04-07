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
        with open(json_path, encoding="utf8") as f:  # Load JSON into a var
            data = json.load(f)

        progress = round((index / total_files) * 100, 2)
        window.write_event_value('-UPDATE_PROGRESS-', progress)

        # Skip system JSONs from Google Takeout that don't belong to media files
        if 'title' not in data or 'photoTakenTime' not in data:
            continue

        titleOriginal = data['title']  # Store metadata into vars
        current_dir = os.path.dirname(json_path)
        rel_dir = os.path.relpath(current_dir, browserPath)
        if rel_dir == ".":
            rel_dir = ""
            
        fixedMediaPath = os.path.join(root_fixed, rel_dir)
        nonEditedMediaPath = os.path.join(root_nonEdited, rel_dir)
        
        os.makedirs(fixedMediaPath, exist_ok=True)
        os.makedirs(nonEditedMediaPath, exist_ok=True)
        
        if current_dir not in mediaMoved:
            mediaMoved[current_dir] = []

        try:
            title = searchMedia(current_dir, titleOriginal, mediaMoved[current_dir], nonEditedMediaPath, editedWord)

        except Exception as e:
            print("Error on searchMedia() with file " + titleOriginal)
            errorCounter += 1
            continue

        filepath = os.path.join(current_dir, title)
        if title == "None":
            print(titleOriginal + " not found")
            errorCounter += 1
            continue

        # METADATA EDITION
        timeStamp = int(data['photoTakenTime']['timestamp'])  # Get creation time
        print(filepath)

        if title.rsplit('.', 1)[1].casefold() in piexifCodecs:  # If EXIF is supported
            try:
                # Récupérer la description si elle existe dans le JSON
                description = data.get('description', '')
                set_EXIF(filepath, data['geoData']['latitude'], data['geoData']['longitude'], data['geoData']['altitude'], timeStamp, description)

            except Exception as e:  # Error handler
                print("Inexistent EXIF data for " + filepath)
                print(str(e))
                errorCounter += 1
                continue

        elif title.rsplit('.', 1)[1].casefold() in videoCodecs:  # If it's a video
            try:
                description = data.get('description', '')
                set_video_metadata(filepath, data['geoData']['latitude'], data['geoData']['longitude'], data['geoData']['altitude'], timeStamp, description)

            except Exception as e:  # Error handler
                print("Error setting video metadata for " + filepath)
                print(str(e))
                errorCounter += 1
                continue

        setWindowsTime(filepath, timeStamp) #Windows creation and modification time

        #MOVE FILE AND DELETE JSON

        os.replace(filepath, os.path.join(fixedMediaPath, title))
        os.remove(json_path)
        mediaMoved[current_dir].append(title)
        successCounter += 1

    window.write_event_value('-UPDATE_DONE-', (successCounter, errorCounter))

from auxFunctions import *
import json
from PIL import Image
import PySimpleGUI as sg

def mainProcess(browserPath, window, editedW):
    piexifCodecs = [k.casefold() for k in ['TIF', 'TIFF', 'JPEG', 'JPG']]
    videoCodecs = [k.casefold() for k in ['MP4', 'MOV', '3GP', 'M4V', 'MKV']]

    mediaMoved = []  # array with names of all the media already matched
    path = browserPath  # source path
    fixedMediaPath = os.path.join(path, "MatchedMedia")  # destination path
    nonEditedMediaPath = os.path.join(path, "EditedRaw")
    errorCounter = 0
    successCounter = 0
    editedWord = editedW or "editado"
    print(editedWord)

    try:
        obj = list(os.scandir(path))  #Convert iterator into a list to sort it
        obj.sort(key=lambda s: len(s.name)) #Sort by length to avoid name(1).jpg be processed before name.jpg
        createFolders(fixedMediaPath, nonEditedMediaPath)
    except Exception as e:
        window.write_event_value('-UPDATE_ERROR-', "Choose a valid directory")
        return

    for entry in obj:
        if entry.is_file() and entry.name.endswith(".json"):  # Check if file is a JSON
            with open(entry, encoding="utf8") as f:  # Load JSON into a var
                data = json.load(f)

            progress = round(obj.index(entry)/len(obj)*100, 2)
            window.write_event_value('-UPDATE_PROGRESS-', progress)

            #SEARCH MEDIA ASSOCIATED TO JSON

            # Skip system JSONs from Google Takeout that don't belong to media files
            if 'title' not in data or 'photoTakenTime' not in data:
                continue

            titleOriginal = data['title']  # Store metadata into vars

            try:
                title = searchMedia(path, titleOriginal, mediaMoved, nonEditedMediaPath, editedWord)

            except Exception as e:
                print("Error on searchMedia() with file " + titleOriginal)
                errorCounter += 1
                continue

            filepath = os.path.join(path, title)
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
            os.remove(os.path.join(path, entry.name))
            mediaMoved.append(title)
            successCounter += 1

    window.write_event_value('-UPDATE_DONE-', (successCounter, errorCounter))

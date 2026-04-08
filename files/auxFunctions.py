import os
import sys
import time
import json
import piexif
import exiftool
from datetime import datetime
from win32_setctime import setctime
from fractions import Fraction

# MEDIA SEARCH & UTILS
def searchMedia(path, title, mediaMoved, nonEdited, editedWord):
    """Searches for the media file associated with a JSON metadata file."""
    title = fixTitle(title)
    # Check for edited version
    realTitle = str(title.rsplit('.', 1)[0] + "-" + editedWord + "." + title.rsplit('.', 1)[1])
    filepath = os.path.join(path, realTitle)
    
    if not os.path.exists(filepath):
        # Check for (1) suffix version
        realTitle = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
        filepath = os.path.join(path, realTitle)
        
        if not os.path.exists(filepath) or os.path.exists(os.path.join(path, title + "(1).json")):
            # Check for exact title match
            realTitle = title
            filepath = os.path.join(path, realTitle)
            
            if not os.path.exists(filepath):
                # Check for duplicate names (recursion)
                realTitle = checkIfSameName(title, title, mediaMoved, 1)
                filepath = os.path.join(path, realTitle)
                
                if not os.path.exists(filepath):
                    # Handle 47 character title limit
                    title = (title.rsplit('.', 1)[0])[:47] + "." + title.rsplit('.', 1)[1]
                    realTitle = str(title.rsplit('.', 1)[0] + "-" + editedWord + "." + title.rsplit('.', 1)[1])
                    filepath = os.path.join(path, realTitle)
                    
                    if not os.path.exists(filepath):
                        realTitle = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
                        filepath = os.path.join(path, realTitle)
                        
                        if not os.path.exists(filepath):
                            realTitle = title
                            filepath = os.path.join(path, realTitle)
                            
                            if not os.path.exists(filepath):
                                realTitle = checkIfSameName(title, title, mediaMoved, 1)
                                filepath = os.path.join(path, realTitle)
                                if not os.path.exists(filepath):
                                    return "None"
    return str(realTitle)

def fixTitle(title):
    """Removes incompatible characters from the filename"""
    bad_chars = '%<>=:?¿*#&{}\\|@!+|"\''
    return str(title).translate(str.maketrans('', '', bad_chars))

def checkIfSameName(title: str, titleFixed, mediaMoved, recursionTime):
    """Recursive function to find a unique name if repeated."""
    if titleFixed in mediaMoved:
        titleFixed = title.rsplit('.', 1)[0] + "(" + str(recursionTime) + ")" + "." + title.rsplit('.', 1)[1]
        return checkIfSameName(title, titleFixed, mediaMoved, recursionTime + 1)
    else:
        return titleFixed

def setWindowsTime(filepath, timeStamp):
    """Sets the Windows file creation and modification timestamps"""
    try:
        setctime(filepath, timeStamp)
        date = datetime.fromtimestamp(timeStamp)
        modTime = time.mktime(date.timetuple())
        os.utime(filepath, (modTime, modTime))
    except Exception as e:
        print(f"Error setting Windows time for {filepath}: {e}")

# GPS & MATH CONVERSIONS
def to_deg(value, loc):
    """Converts decimal coordinates into (degrees, minutes, seconds, direction)"""
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    min = int(t1)
    sec = round((t1 - min) * 60, 5)
    return (deg, min, sec, loc_value)

def change_to_rational(number):
    """Converts a number to a rational (numerator, denominator) tuple"""
    f = Fraction(str(number))
    return (f.numerator, f.denominator)

# PHOTO METADATA (PIEXIF)
def set_photo_metadata(filepath, lat, lng, altitude, timeStamp, description=""):
    """Sets EXIF metadata for image files using the piexif library"""
    try:
        exif_dict = piexif.load(filepath)
    except Exception:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y:%m:%d %H:%M:%S")
    
    if '0th' not in exif_dict: exif_dict['0th'] = {}
    if 'Exif' not in exif_dict: exif_dict['Exif'] = {}

    exif_dict['0th'][piexif.ImageIFD.DateTime] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = dateTime

    if description:
        exif_dict['0th'][piexif.ImageIFD.ImageDescription] = description.encode('utf-8')

    # GPS Injection
    if lat != 0.0 or lng != 0.0:
        try:
            lat_deg = to_deg(lat, ["S", "N"])
            lng_deg = to_deg(lng, ["W", "E"])

            exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
            exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

            exif_dict['GPS'] = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSAltitudeRef: 1 if altitude < 0 else 0,
                piexif.GPSIFD.GPSAltitude: change_to_rational(round(abs(altitude), 2)),
                piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
                piexif.GPSIFD.GPSLatitude: exiv_lat,
                piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
                piexif.GPSIFD.GPSLongitude: exiv_lng,
            }
        except Exception:
            pass

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)

# VIDEO METADATA (EXIFTOOL)
def get_exiftool_path():
    """Locates ExifTool and handles automatic renaming of 'exiftool(-k).exe' for better UI experience"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exiftool_exe = os.path.join(script_dir, "exiftool.exe")
    exiftool_lib = os.path.join(script_dir, "exiftool_files")
    
    # Handle the (-k) version renaming for easier setup (else exiftool crash)
    exiftool_to_format = os.path.join(script_dir, "exiftool(-k).exe")
    if os.path.exists(exiftool_to_format):
        try:
            os.rename(exiftool_to_format, exiftool_exe)
        except Exception:
            pass # hmm idk becanse exiftool can't work whithout this rename 


    # Exiftool work only in the folder "files" so in the same folder of the main file (window.py)
    if not os.path.isfile(exiftool_exe) or not os.path.isdir(exiftool_lib):
        print("\n[CRITICAL ERROR] Missing ExifTool dependencies!")
        print(f"Ensure 'exiftool.exe' (or 'exiftool(-k).exe' and 'exiftool_files/' are in: {script_dir}")
        sys.exit(1)

    return exiftool_exe

def set_video_metadata(filepath, lat, lng, altitude, timeStamp, description="", camera_make="", camera_model="", author="", software=""):
    """Injects metadata into video files using ExifTool"""
    dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y:%m:%d %H:%M:%S")

    # All the datas to transfer
    tags = {
        "AllDates": dateTime,            # Sets DateTimeOriginal, CreateDate, ModifyDate
        "Keys:CreationDate": dateTime, 
        "Artist": author,
        "Author": author,
        "Make": camera_make,
        "Model": camera_model,
    }

    if description:
        tags["Description"] = description
        tags["ImageDescription"] = description
        tags["Title"] = description
        tags["ItemList:Title"] = description
        tags["ItemList:Description"] = description

    if lat != 0.0 or lng != 0.0:
        tags["Keys:GPSCoordinates"] = f"{lat} {lng} {altitude}"
        tags["UserData:GPSCoordinates"] = f"{lat} {lng} {altitude}"
        # Standard GPS tags
        tags["GPSLatitude"] = lat
        tags["GPSLongitude"] = lng
        tags["GPSAltitude"] = altitude

    if software: # example : CapCut / adobe / Da Vinci...
        tags["Software"] = software
        tags["CreatorTool"] = software
        tags["HandlerDescription"] = software

    exiftool_path = get_exiftool_path()
    try:
        with exiftool.ExifToolHelper(executable=exiftool_path) as et:
            et.set_tags([filepath], tags=tags, params=["-overwrite_original"])
    except Exception as e:
        print(f"ExifTool error for {filepath}: {e}")
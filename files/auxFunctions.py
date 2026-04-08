import os
import time
from datetime import datetime
import piexif
from win32_setctime import setctime
from fractions import Fraction
import exiftool
import sys 
from fractions import Fraction

# Function to search media associated to the JSON
def searchMedia(path, title, mediaMoved, nonEdited, editedWord):
    title = fixTitle(title)
    realTitle = str(title.rsplit('.', 1)[0] + "-" + editedWord + "." + title.rsplit('.', 1)[1])
    filepath = os.path.join(path, realTitle)  # First we check if exists an edited version of the image
    if not os.path.exists(filepath):
        realTitle = str(title.rsplit('.', 1)[0] + "(1)." + title.rsplit('.', 1)[1])
        filepath = os.path.join(path, realTitle)  # First we check if exists an edited version of the image
        if not os.path.exists(filepath) or os.path.exists(os.path.join(path, title + "(1).json")):
            realTitle = title
            filepath = os.path.join(path, realTitle)  # If not, check if exists the path with the same name
            if not os.path.exists(filepath):
                realTitle = checkIfSameName(title, title, mediaMoved, 1)  # If not, check if exists the path to the same name adding (1), (2), etc
                filepath = os.path.join(path, realTitle)
                if not os.path.exists(filepath):
                    title = (title.rsplit('.', 1)[0])[:47] + "." + title.rsplit('.', 1)[1]  # Sometimes title is limited to 47 characters, check also that
                    realTitle = str(title.rsplit('.', 1)[0] + "-editado." + title.rsplit('.', 1)[1])
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
                                if not os.path.exists(filepath):  # If path not found, return null
                                    realTitle = None
                        else:
                            filepath = os.path.join(path, title)  # Move original media to another folder
                            os.replace(filepath, os.path.join(nonEdited, title))
                    else:
                        filepath = os.path.join(path, title)  # Move original media to another folder
                        os.replace(filepath, os.path.join(nonEdited, title))
        else:
            filepath = os.path.join(path, title)  # Move original media to another folder
            os.replace(filepath, os.path.join(nonEdited, title))
    else:
        filepath = os.path.join(path, title)  # Move original media to another folder
        os.replace(filepath, os.path.join(nonEdited, title))

    return str(realTitle)


# Supress incompatible characters
def fixTitle(title):
    bad_chars = '%<>=:?¿*#&{}\\|@!+|"\''
    return str(title).translate(str.maketrans('', '', bad_chars))

# Recursive function to search name if its repeated
def checkIfSameName(title, titleFixed, mediaMoved, recursionTime):
    if titleFixed in mediaMoved:
        titleFixed = title.rsplit('.', 1)[0] + "(" + str(recursionTime) + ")" + "." + title.rsplit('.', 1)[1]
        return checkIfSameName(title, titleFixed, mediaMoved, recursionTime + 1)
    else:
        return titleFixed

def createFolders(fixed, nonEdited):
    if not os.path.exists(fixed):
        os.mkdir(fixed)

    if not os.path.exists(nonEdited):
        os.mkdir(nonEdited)

def setWindowsTime(filepath, timeStamp):
    setctime(filepath, timeStamp)  # Set windows file creation time
    date = datetime.fromtimestamp(timeStamp)
    modTime = time.mktime(date.timetuple())
    os.utime(filepath, (modTime, modTime))  # Set windows file modification time

def to_deg(value, loc):
    """convert decimal coordinates into degrees, munutes and seconds tuple
    Keyword arguments: value is float gps-value, loc is direction list ["S", "N"] or ["W", "E"]
    return: tuple like (25, 13, 48.343 ,'N')
    """
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
    """convert a number to rational
    Keyword arguments: number
    return: tuple like (1, 2), (numerator, denominator)
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def set_EXIF(filepath, lat, lng, altitude, timeStamp, description=""):
    """"
    Sets EXIF metadata (date, description, and GPS) for an image file using piexif.
    """
    
    exif_dict = piexif.load(filepath)

    dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y:%m:%d %H:%M:%S")  # Create date object
    
    # Initialize the dictionaries if they do not exist in the original image
    if '0th' not in exif_dict: exif_dict['0th'] = {}
    if 'Exif' not in exif_dict: exif_dict['Exif'] = {}

    exif_dict['0th'][piexif.ImageIFD.DateTime] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = dateTime
    exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = dateTime

    if description:
        exif_dict['0th'][piexif.ImageIFD.ImageDescription] = description.encode('utf-8')

    exif_bytes = piexif.dump(exif_dict)
    piexif.insert(exif_bytes, filepath)


    try:
        exif_dict = piexif.load(filepath)
        lat_deg = to_deg(lat, ["S", "N"])
        lng_deg = to_deg(lng, ["W", "E"])

        exiv_lat = (change_to_rational(lat_deg[0]), change_to_rational(lat_deg[1]), change_to_rational(lat_deg[2]))
        exiv_lng = (change_to_rational(lng_deg[0]), change_to_rational(lng_deg[1]), change_to_rational(lng_deg[2]))

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
        }

        exif_dict['GPS'] = gps_ifd

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filepath)

    except Exception as e:
        print("Coordinates not settled")
        pass

def get_exiftool_path():
    """
    Locates ExifTool and handles the automatic renaming of the (-k) version.
    Ensures the 'files' directory structure is respected.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    exiftool_exe = os.path.join(script_dir, "exiftool.exe")
    exiftool_lib = os.path.join(script_dir, "exiftool_files")
    
    # Auto-rename the '(-k)' version if found
    exiftool_to_format = os.path.join(script_dir, "exiftool(-k).exe")
    if os.path.exists(exiftool_to_format):
        try:
            os.rename(exiftool_to_format, exiftool_exe)
        except Exception as e:
            print(f"Warning: Could not rename exiftool(-k).exe: {e}")

    # Strict validation
    if not os.path.isfile(exiftool_exe) or not os.path.isdir(exiftool_lib):
        print("\n[CRITICAL ERROR] Missing dependencies in the 'files' directory!")
        print(f"Ensure 'exiftool.exe' and 'exiftool_files/' are in: {script_dir}")
        sys.exit(1)

    return exiftool_exe

def set_metadata_optimal(filepath, lat, lng, altitude, timeStamp, description="", camera_make="", camera_model="", author="", software=""):
    """
    Injects all possible metadata using ExifTool for an optimal transfer
    """
    # Format the date (YYYY:MM:DD HH:MM:SS)
    dateTime = datetime.fromtimestamp(timeStamp).strftime("%Y:%m:%d %H:%M:%S")

    # All the datas to transfer
    tags = {
        # Date and Time
        "AllDates": dateTime,            # Sets DateTimeOriginal, CreateDate, and ModifyDate
        "Keys:CreationDate": dateTime,   # Essential for Apple/QuickTime
        
        # Device and author
        "Artist": author,                # Who took the photo (Standard EXIF)
        "Author": author,                # XMP version
        "Make": camera_make,             # Device Manufacturer (e.g., Apple, Samsung)
        "Model": camera_model,           # Device Model (e.g., iPhone 15)
        
        # Inject to the metadatas that is GPM who had edited and linked the medias 
        # Optional ; )
        # "Software": "GooglePhotosMatcher", 
        # It is defined lower 
    }

    # Description and Title
    if description:
        tags["Description"] = description
        tags["ImageDescription"] = description
        tags["ItemList:Description"] = description
        tags["Title"] = description
        tags["ItemList:Title"] = description

    # Location of the video
    if lat != 0.0 or lng != 0.0:
        # Standard GPS Tags
        tags["GPSLatitude"] = lat
        tags["GPSLongitude"] = lng
        tags["GPSAltitude"] = altitude
        # Video-specific location tags (QuickTime/Keys)
        tags["Keys:GPSCoordinates"] = f"{lat} {lng} {altitude}"
        tags["UserData:GPSCoordinates"] = f"{lat} {lng} {altitude}"
        
    
    if software:
        # Adobe, Capcut...
        tags["Software"] = software


    exiftool_path = get_exiftool_path()
    
    try:
        with exiftool.ExifToolHelper(executable=exiftool_path) as et:
            # -overwrite_original: saves space by not creating backup files
            et.set_tags([filepath], tags=tags, params=["-overwrite_original"])
    except Exception as e:
        print(f"Error applying metadata to {filepath}: {e}")
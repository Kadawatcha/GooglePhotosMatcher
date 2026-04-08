# Note to future / current devs:

For all the steps below, you need to:

**Create a virtual environment at the root of the project: `python -m venv venv`**


## DEVELOPER NOTE: Generate the final .exe 

1) Execute `pip install -r "requirements-dev.txt"` to install the libraries required to create the .exe file

2) Download exiftool from https://exiftool.org/ [this link](https://sourceforge.net/projects/exiftool/files/exiftool-13.55_64.zip/download) for the 64bits version direct download

3) Rename 'exiftool(-k).exe' to 'exiftool.exe'

4) Put 'exiftool.exe' and the folder 'exiftool_files' at the root of the project

5) Run the following command in your terminal from the project root:

```pyinstaller --noconsole --onefile --icon=assets/photos.ico --name "GPMatcher" --distpath "." --add-data "exiftool.exe;." --add-data "assets/photos.ico;." --paths files files/window.py```

The 'GPMatcher.exe' file is now ready ! You can open it from your file explorer to start matching your photos and videos !

---

## DEVELOPER NOTE: Python version (no .exe file)

*You can also run the app without the .exe file. Here are the steps:*
 

1) Execute `pip install -r "requirements.txt"` for basic usage (e.g., matching photos)

2) Run the file 'window.py'

3) Go match your photos!

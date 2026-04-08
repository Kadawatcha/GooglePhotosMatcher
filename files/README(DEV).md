# Note to futures dev / for actuals devs :

For alls this step lower you need to :

**Create a virtual environement at the root of the project `python -m venv venv`**


## DEVELOPER NOTE: generate the final .exe 

1) Execute `pip install -r "requirements-dev.txt"` for have the libs to create the .exe file

2) Download exiftool from https://exiftool.org/ [this link](https://sourceforge.net/projects/exiftool/files/exiftool-13.55_64.zip/download) for the 64bits version

3) Rename 'exiftool(-k).exe' to 'exiftool.exe'

4) Put 'exiftool.exe' and the folder 'exiftool_files' at the root of the project

5) Run the following command in your terminal from the project root:

```pyinstaller --noconsole --onefile --icon=assets/photos.ico --name "GPMatcher" --distpath "." --add-data "exiftool.exe;." --add-data "assets/photos.ico;." --paths files files/window.py```

And the 'GPMatcher.exe' file is ready ! Go in your file explorer and you can open to match your photos / videos

## DEVELOPER NOTE: Python version no .exe file

*you can also run the app without .exe file, steps to do it:*
 

1) execute `pip install -r "requirements.txt"` for basic use : match photos...

2) run the file 'window.py' 

3) Go match your photos !






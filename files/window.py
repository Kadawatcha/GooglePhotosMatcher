import threading
import PySimpleGUI as sg
from main import mainProcess
import ctypes
from auxFunctions import resource_path
import os

# High definition of the window (very very very better UI )
ctypes.windll.shcore.SetProcessDpiAwareness(1)

sg.theme("DarkTeal2")

layout = [
    [sg.T("")],
    [sg.Text('Enter suffix used for edited photos (optional):')],
    [sg.InputText(key='-INPUT_TEXT-'), sg.ReadFormButton('Help')],
    [sg.T("")],
    [sg.Text("Choose Google Takeout folder: ")],
    [sg.Input(key="-IN2-", change_submits=True), sg.FolderBrowse(key="-IN-")],
    [sg.T("")],
    [sg.Button("Match", size=(10, 1))],
    [sg.T("")],
    [sg.ProgressBar(100, visible=False, orientation='h', border_width=4, key='-PROGRESS_BAR-')],
    [sg.T("", key='-PROGRESS_LABEL-', size=(50, 1))]
]
# serch logo (for compatibility windows and python)
icon_path = resource_path("assets/photos.ico")
if not os.path.exists(icon_path):
    icon_path = resource_path("photos.ico")

window = sg.Window('Google Photos Matcher',
                   layout, 
                   icon=icon_path, 
                   finalize=True,)

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break
        
    elif event == "Match":
        if not values["-IN2-"]:
            sg.popup_error("Please select a folder first!")
            continue
            
        window['Match'].update(disabled=True)
        window['-PROGRESS_LABEL-'].update("Initializing...", visible=True, text_color='white')
        window['-PROGRESS_BAR-'].update(0, visible=True)
        
        # Start processing in a separate thread to keep UI responsive
        threading.Thread(
            target=mainProcess, 
            args=(values["-IN2-"], window, values['-INPUT_TEXT-']), 
            daemon=True
        ).start()

    elif event == '-UPDATE_PROGRESS-':
        progress = values[event]
        window['-PROGRESS_LABEL-'].update(f"Progress: {progress}%", visible=True)
        window['-PROGRESS_BAR-'].update(progress, visible=True)

    elif event == '-UPDATE_ERROR-':
        window['-PROGRESS_LABEL-'].update(values[event], visible=True, text_color='red')
        window['Match'].update(disabled=False)

    elif event == '-UPDATE_DONE-':
        success, errors = values[event]
        window['-PROGRESS_BAR-'].update(100)
        msg = f"Done! {success} successes, {errors} errors."
        window['-PROGRESS_LABEL-'].update(msg, visible=True, text_color='#c0ffb3')
        window['Match'].update(disabled=False)

    elif event == "Help":
        sg.Popup("Information", 
                 "Google Photos often downloads two versions: 'Photo.jpg' and 'Photo-edited.jpg'.\n\n"
                 "The suffix depends on your Google account language.\n"
                 "Example (Spain): 'editado'\n"
                 "Example (France): 'modifié'\n\n"
                 "If left blank, 'editado' is used by default.", 
                 icon=resource_path("assets/photos.ico"))

window.close()
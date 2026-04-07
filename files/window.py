from main import *
import threading

sg.theme("DarkTeal2")
layout = [[sg.T("")],
          [sg.Text('Enter suffix used for edited photos (optional):')],
          [sg.InputText(key='-INPUT_TEXT-'), sg.ReadFormButton('Help')],
          [sg.T("")],
          [sg.Text("Choose a folder: ")],
          [sg.Input(key="-IN2-", change_submits=True), sg.FolderBrowse(key="-IN-")],
          [sg.T("")],
          [sg.Button("Match")],
          [sg.T("")],
          [sg.ProgressBar(100, visible=False, orientation='h', border_width=4, key='-PROGRESS_BAR-')],
          [sg.T("", key='-PROGRESS_LABEL-')]]

window = sg.Window('Google Photos Matcher', layout, icon='photos.ico')

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == "Exit":
        break
    elif event == "Match":
        window['Match'].update(disabled=True)
        window['-PROGRESS_LABEL-'].update("Starting...", visible=True, text_color='white')
        window['-PROGRESS_BAR-'].update(0, visible=True)
        threading.Thread(target=mainProcess, args=(values["-IN2-"], window, values['-INPUT_TEXT-']), daemon=True).start()
    elif event == '-UPDATE_PROGRESS-':
        progress = values[event]
        window['-PROGRESS_LABEL-'].update(str(progress) + "%", visible=True, text_color='white')
        window['-PROGRESS_BAR-'].update(progress, visible=True)
    elif event == '-UPDATE_ERROR-':
        window['-PROGRESS_LABEL-'].update(values[event], visible=True, text_color='red')
        window['Match'].update(disabled=False)
    elif event == '-UPDATE_DONE-':
        successCounter, errorCounter = values[event]
        sucessMessage = " success" if successCounter == 1 else " successes"
        errorMessage = " error" if errorCounter == 1 else " errors"
        window['-PROGRESS_BAR-'].update(100, visible=True)
        msg = "Matching process finished with " + str(successCounter) + sucessMessage + " and " + str(errorCounter) + errorMessage + "."
        window['-PROGRESS_LABEL-'].update(msg, visible=True, text_color='#c0ffb3')
        window['Match'].update(disabled=False)
    elif event == "Help":
        sg.Popup("", "Media edited with the integrated editor of google photos "
                 "will download both the original image 'Example.jpg' and the edited version 'Example-editado.jpg'.", "",
                "The 'editado' suffix changes depending on the language (in the case of Spain it will be 'editado').","",
                "If you leave this box blank default spanish suffix will be used to search for edited photos.",
                 "", title="Information", icon='photos.ico')

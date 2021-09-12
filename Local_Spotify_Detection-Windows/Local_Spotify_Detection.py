from io import StringIO
from SwSpotify import spotify, SpotifyClosed, SpotifyNotRunning, SpotifyPaused
from flask import Flask
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS']  = False
PORT_NUMBER = 8080


### SwSpotify Exceptions ###
class SpotifyNotRunning(Exception):
    """
    Base exception raised if Spotify is not running i.e. is closed or paused.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, message="Spotify appears to be paused or closed at the moment."):
        super().__init__(message)


class SpotifyPaused(SpotifyNotRunning):

    def __init__(self, message="Spotify appears to be paused at the moment."):
        super().__init__(message)


class SpotifyClosed(SpotifyNotRunning):

    def __init__(self, message="Spotify appears to be closed at the moment."):
        super().__init__(message)

### SwSpotify Main Windows Function ###
def get_info_windows():
    """
    Reads the window titles to get the data.
    Older Spotify versions simply use FindWindow for "SpotifyMainWindow",
    the newer ones create an EnumHandler and flood the list with
    Chrome_WidgetWin_0s
    """

    import win32gui

    windows = []

    old_window = win32gui.FindWindow("SpotifyMainWindow", None)
    old = win32gui.GetWindowText(old_window)

    def find_spotify_uwp(hwnd, windows):
        text = win32gui.GetWindowText(hwnd)
        classname = win32gui.GetClassName(hwnd)
        if classname == "Chrome_WidgetWin_0" and len(text) > 0:
            windows.append(text)

    if old:
        windows.append(old)
    else:
        win32gui.EnumWindows(find_spotify_uwp, windows)

    # If Spotify isn't running the list will be empty
    if len(windows) == 0:
        raise SpotifyClosed

    # Local songs may only have a title field
    try:
        artist, track = windows[0].split(" - ", 1)
    except ValueError:
        artist = ""
        track = windows[0]

    # The window title is the default one when paused
    if windows[0].startswith("Spotify"):
        raise SpotifyPaused

    return track, artist


@app.route('/')
def index():
    try:
        title, artist = get_info_windows()
        print("Spotify Currently Playing")
        return {
            "currently_playing": title + '-' + artist
        }
    except SpotifyPaused as e:
        print('Paused')
        return {
            "error": "Paused"
        }
    except SpotifyClosed as e:
        print('Closed')
        return {
            "error": "Closed"
        }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT_NUMBER)

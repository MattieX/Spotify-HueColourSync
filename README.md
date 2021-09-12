# Spotify-HueColourSync
A Flask App to return Currently Playing Song Information from the Official & Non Official Spotify API, with support to sync artwork to Philips Hue Lights using Node-Red.


## Features
* Retrieve Multiple Details From the Currently Playing Spotify API, including Artist and Album artwork
* Retrieve Artist Cover Images from the Unofficial Spotify API
* Detect Locally Playing Content Before Querying API To Hinder Any Rate Limiting
* Sync Philips Hue Lights To Either Album Artwork, Artist Image or Artist Cover Image of a Song - Each Light Will Take a Portion of the Image to Generate a Satisfying Colour Palette

### Sample Output Per Request
```yaml
{
  "artistImages": [
    [
      "6nS5roXSAGhTGr34W6n7Et",
      "Disclosure",
      "https://i.scdn.co/image/ab6761610000e5eb784a17787904570df53ae9a2"
    ],
    [
      "2wY79sveU1sp5g7SokKOiI",
      "Sam Smith",
      "https://i.scdn.co/image/ab6761610000e5ebe5a4f8ec6996364b2f824fcb"
    ]
  ],
  "currentlyPlaying": {
    "song_name": "Latch",
    "song_id": "51ODNNDZm21HU7wI7cccRr",
    "album_name": "Settle (Special Edition)",
    "album_id": "7bdjtx1RTkWoSoOaIl7a8E",
    "album_picture": "https://i.scdn.co/image/ab67616d0000b273786201dca187d2b0c956c24b",
    "artist_names": [
      "Disclosure",
      "Sam Smith"
    ],
    "artist_ids": [
      "6nS5roXSAGhTGr34W6n7Et",
      "2wY79sveU1sp5g7SokKOiI"
    ],
    "is_playing": true
  },
  "currentArtistImage": "https://i.scdn.co/image/ab6761610000e5eb784a17787904570df53ae9a2",
  "artistHeaderImage": "https://i.scdn.co/image/ab6761860000101618b19e7b78bb0a081c4b32db"
}
```


## Why have I made this?
Since trying the Official Hue Sync App with music I found it too unpredictable and largely un-related to the song so I wouldn't would use it regularly. Therefore, obtaining the colours from Spotify Artwork using the API and distributing a portion of each image throughout my Philips Hue Lights was more desirable for me.

## What will it do?
* When configured with all the pre-requisites, so long as you have the Home Assistant `Sync Or Not` Toggle set to `ON` (See Below) every time you play a new song on your Spotify Desktop Client, your Hue Lights will change colour.
* The dropdown toggle (See Below) will allow you to have your music sync to the `Album Cover`, `Artist Picture` or `Artist Cover Image`
* Optionally, you can go to the Application's URL yourself to use the JSON for any purpose you would like

## Pre-Requisites
* Access to the IP Address of the Container when bound to the Docker Host on a NON-HEADLESS system to initialise Spotify O-Auth - **REQUIRED**
* Philips Hue or Similar Lighting Products (May Require Manual Tweaking) - **OPTIONAL**
* Home Assistant + Node-Red Instance - **OPTIONAL**

# Docker Configuration
| Environment variable | Description | Notes |
|:---:|---|---|
| `REDIS_HOST` | IP Address of Redis Docker Container | **Required** |
| `REDIS_PORT` | Port for Redis Container (Recommend to leave as 6379) | **Required** - Default Redis Port is `6379` which can be overridden with a `redis.conf` |
| `SPOTIFY_CLIENT_ID` | Spotify Client ID From Dev API | **Required**  - Obtain From https://developer.spotify.com/dashboard/ |
| `SPOTIFY_CLIENT_SECRET` | Spotify Client Secret from Dev API | **Required** - Obtain From https://developer.spotify.com/dashboard/ |
| `SPOTIFY_REDIRECT_URL` | Full URL You Use to Access the App e.g. `http://<docker-host-ip>:5000` if binding to host port | **Required** -  Set At https://developer.spotify.com/dashboard/ |
| `FLASK_SECRET_KEY` | Random String Used for Cookie Signing | **Required** -  See Recommended Practice to Set Secret Key [here](https://newbedev.com/where-do-i-get-a-secret-key-for-flask)|

**This App Uses Port `5000` Internally for the Flask Server, therefore either route to this port with a Reverse Proxy, or bind it to a different port externally in the `ports` section of the `docker-compose.yaml`**
E.g.
```yaml
ports:
  - 6000:5000 # External:Internal
```
##
## Getting Started (Docker)
* Download the Git Repository
* Configure the Environment Variables explained above in `docker-compose.yaml`, then run `docker-compose up -d`. This will `Build` the Docker the Image Automatically the first time
* Access the IP that is bound to the Docker Host in your Browser, **on each container restart you will be prompted to log-in with your Spotify Credentials** - This is a necessary Authorisation Flow Procedure that is required in order to obtain parts of the Spotify API That pertain to key scopes about your account (E.g. Currently Playing, What Devices are Playing...)

![image](https://user-images.githubusercontent.com/21284075/133000659-5869a2bf-81df-47e5-9fcb-fcc078723df0.png)

* If something is playing on Spotify on your account, manually refreshing this page now will show the Song Information

# Spotify Developer API Configuration
* Please Login To https://developer.spotify.com/dashboard/ using your Spotify Credentials
* Press Create an App, Give it a Name & Description
* Note Down the Apps `Client ID` and `Client Secret` once created and Fill These into the **Docker Environment Variables**

# Windows Local Spotify Detection Script
## What is it and why is it necessary?
* This Script is currently required in order for the Node-Red flow to function. It runs a very simple Flask App.
* This script utilises the `win32gui` module to check if Spotify is open on your Windows machine, and `SwSpotify` is used to determine what track is playing based on the window title
* The Node-Red Flow will query this script by default `Every 1 Second` to decide whether a Request to the External Spotify API Is Necessary - else you would likely be rate limited very quickly.
## Requirements
* Windows System (For Now...)
* Spotify Desktop Installed
* Python
* Requirements.txt file in the same folder as the `Local_Spotify_Detectection.py` Script to be installed with `pip install -r requirements.txt`
* Node - **Optional**
## Recommended Running Practices
* Personally I use [Node-Forever](https://www.npmjs.com/package/forever) combined with a simple `batch script` to run this Script in the Background on Boot. Node-Red will poll this script every second

```batch
cd C:\Users\<Username>
forever start -c python .\Documents\Github\Spotify-HueColourSync\Local_Spotify_Detection-Windows\Local_Spotify_Detection.py
```

* The Batch Script is Placed in the Windows Start-Up Folder: `C:\Users\<Username>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup`



# Home-Assistant Configuration
Add the following to your `configuration.yaml`
```yaml
input_boolean:
  album_or_artist:
    name: Music to Sync to Album or Artist
    icon: mdi:music

  sync_or_not:
    name: Sync Spotify to Lights or Not
    icon: mdi:autorenew
```
Navigate to `Configuration` ➡️ `Helpers`
Configure a `Dropdown` Helper like this
<details>
<summary>:arrow_down: View Helper Configuration Image</summary>
<img src="https://user-images.githubusercontent.com/21284075/132997416-fbbf2b63-d523-4321-8b5a-4e922a46ead0.png" width="500">
</details>

* Import the following into your Dashboard By Adding a Manual Tile and Pasting the YAML below
```yaml
type: entities
entities:
  - entity: input_boolean.sync_or_not
    name: Sync Or Not
  - entity: input_select.album_artist_or_artist_cover_image
title: Sync Hue Music
```
<details>
<summary>:arrow_down: View Home Assistant Tile</summary>
<img src="https://user-images.githubusercontent.com/21284075/132999418-fc3fd585-c21e-415d-93a6-f8d04d102542.png" width="500">
</details>

# Node-Red Configuration
* Import the Node-Red Script by heading to the top right of Node-Red and pasting in the contents of the `Node-Red_Spotify-HueColourSync.json` into the textbox that appears

![image](https://user-images.githubusercontent.com/21284075/133000865-d2e441ef-53eb-46e1-8bf4-93296b5e92b0.png)

<details>
<summary>:arrow_down: View Node-Red Topology</summary>
<img src="https://user-images.githubusercontent.com/21284075/133001637-2f732c81-e236-4327-a981-08a369cd74c9.png" width="1000">
</details>


* Modify the Second Node in the Flow to contain the Flask Script IP:PORT Running on Windows and on Docker
![image](https://user-images.githubusercontent.com/21284075/133000564-cec9695a-4e35-4b50-9d23-adee29b4ed50.png)

* Modify the `Entity id` for each Hue Light (Final Row of Nodes In the Flow)
* Modify the `Entity id` inside each of the `Format Payload` Functions

![image](https://user-images.githubusercontent.com/21284075/133001085-1fd4c913-caa1-4f0f-a95a-b9b640f0edd4.png)

**Some Understanding of JavaScript and Node-Red will allow you to increase or decrease the amount of lights in this script, or use different light sources entirely.**

* Add the Following Code to your Home Assistant Node-Red Configuration Pane Under `Supervisor` ➡️ `Integrations` ➡️ `Node-Red` ➡️ `Configuration`
```yaml
npm_packages:
  - jimp
  - color-convert
```
* Modify Settings.js
With the `vscode` nodered integration, browse to: `node-red` ➡️ `settings.js` and modify the following part of code to include the following
```javascript
  functionGlobalContext: {
    Jimp:require('jimp'),
    convertColor:require('color-convert')
  },
```
**Be Sure to Restart your Node-Red Instance After Adding These Packages!**

# Future Development
* TBC :hourglass:


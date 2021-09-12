from flask import Flask, session, jsonify, request
from flask_session import Session
from spotipy import oauth2
import time, os, redis, requests, spotipy

### Docker Environment Variables ###
REDIS_HOST = os.environ['REDIS_HOST']
REDIS_PORT = os.environ['REDIS_PORT']
SPOTIPY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = os.environ['SPOTIFY_REDIRECT_URL']
SECRET_KEY = os.environ['FLASK_SECRET_KEY']
REDIS_URL = "redis://" + REDIS_HOST + ":" + REDIS_PORT

### Flask Configuration ###
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['JSON_SORT_KEYS']  = False
app.config['SESSION_REDIS'] = redis.from_url(REDIS_URL)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SECRET_KEY'] = SECRET_KEY

# Establish Flask Session
server_session = Session(app)

### Spotipy Settings ###
SCOPE = ["user-library-read", "user-read-currently-playing", "user-read-playback-state"]
CACHE = '.spotipyoauthcache'
# Initialise Spotipy Connection
sp_oauth = oauth2.SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET,
                               redirect_uri=SPOTIPY_REDIRECT_URI,scope=SCOPE,cache_path=CACHE)


"""
Deals with the Main Script Logic, calling Official API Functions and Unofficial APIFunctions
Returns a JSON Dictionary containing information regarding the currently playing spotify song
"""
@app.route('/')
def mainLogic():
    # On Each API Request, Check if Redis is Running
    is_redis_up = checkRedisUp()
    if (is_redis_up):
        # Initialise Empty Access_Token
        official_access_token = ""
        cached_access_token_dict = sp_oauth.get_cached_token()

        # If there is a valid access token in memory already, set it
        if cached_access_token_dict:
            print("Found a cached official access token!")
            official_access_token = cached_access_token_dict['access_token']

        # No Official Access Token Present, go and get one
        else:
            print(f"Request URL: {request.url}")
            request_url = request.url
            oauth_parsed_response_code = sp_oauth.parse_response_code(request_url)
            if oauth_parsed_response_code != request_url:
                print("Found Spotify auth code in Request URL! Trying to get valid access token...")
                cached_access_token_dict = sp_oauth.get_access_token(oauth_parsed_response_code)
                official_access_token = cached_access_token_dict['access_token']

        # If the access token is available... Use it.
        if official_access_token:
            print("Official Access token available! Trying to get current song information...")
            print(f"Official Spotify Access Token: {official_access_token}")
            sp = spotipy.Spotify(official_access_token)
            currently_playing_json = sp.currently_playing(market='GB')
            # If something is returned from the Currently Playing API (Song Paused or Playing)
            if currently_playing_json is not None:
                if (currently_playing_json['is_playing'] == True):

                    ### OFFICIAL API ###
                    # Get the currently Playing Dictionary using API
                    currently_playing_dictionary = parseCurrentlyPlaying(currently_playing_json)
                    # Return an artist image list
                    artist_images_list = parseArtists(currently_playing_dictionary['artist_ids'], sp)
                    # Zip the artist NAME, ID and IMAGE lists together in a 1-1-1 relationship
                    artist_dictionary = list(zip(currently_playing_dictionary['artist_ids'], currently_playing_dictionary['artist_names'], artist_images_list))
                    # Access 1st Artist's [0] Spotify Artist Image [2]
                    artist_image = artist_dictionary[0][2]

                    ### UNOFFICIAL API ###
                    # Handle the Artist Cover Image
                    unauth_token_response = mainUnauthLogic()
                    unofficial_access_token = unauth_token_response['unofficial_access_token']
                    print(f"Unofficial Spotify Access Token: {unofficial_access_token}")

                    # Use First Listed Artist On the Song for the Header Image
                    first_artist_id = artist_dictionary[0][0]
                    artist_header_image_response = getArtistHeaderImage(unofficial_access_token, first_artist_id)
                    # Only set the artist header image if the artist has one
                    artist_header_image = artist_header_image_response['data']['artist']['visuals']['headerImage']['sources'][0]['url'] if artist_header_image_response['data']['artist']['visuals']['headerImage'] != None else 'null'

                    # Constructing Final API Output to Return
                    api_output_dictionary =  {
                        "artistImages": artist_dictionary,
                        "currentlyPlaying" : currently_playing_dictionary,
                        "currentArtistImage": artist_image,
                        "artistHeaderImage": artist_header_image
                    }
                    return api_output_dictionary

                # Song is Paused
                else:
                    return {
                            "Debug": "Spotify is Paused",
                    }

            # Spotify API Didn't Return Anything - Spotify is Closed
            else:
                return {
                        "Debug": "Spotify is closed or Open but Dormant",
                }

        # If user is not logged in, get them to log in...
        else:
            return htmlForLoginButton()
    else:
        print('=====================================================================================')
        print("The Server could not start because a connection to the Redis Server could not be made")
        print('=====================================================================================')
        return {
            'Debug': "You need to start the redis server. It can't be contacted"
        }


"""Returns a basic Login Button for the Spotify API"""
def htmlForLoginButton():
    auth_url = getSPOauthURI()
    htmlLoginButton = "<a href='" + auth_url + "'>Login to Spotify</a>"
    return htmlLoginButton


"""Returns True or False depending if we can contact the REDIS Server"""
def checkRedisUp():
    try:
        r = redis.Redis(REDIS_HOST, socket_connect_timeout=1, port=REDIS_PORT) # short timeout for the test
        print(f"Redis {r}")
        r.ping()
        print('Successfully Connected To Redis "{}"'.format(REDIS_HOST))
        return True

    except redis.exceptions.TimeoutError as e:
        print('There was an error connecting to Redis...')
        return False


"""Returns the Currently Used URL For Spotify O-Auth"""
def getSPOauthURI():
    auth_url = sp_oauth.get_authorize_url()
    return auth_url


"""Returns a custom dictionary from the spotify API Request for the Currently Playing Track"""
def parseCurrentlyPlaying(currently_playing_json):
    song_name = currently_playing_json['item']['name']
    song_id = currently_playing_json['item']['id']
    album_name = currently_playing_json['item']['album']['name']
    album_id = currently_playing_json['item']['album']['id']
    album_picture = currently_playing_json['item']['album']['images'][0]['url']
    artists = [artist for artist in currently_playing_json['item']['artists']]
    is_playing = currently_playing_json['is_playing']

    artist_name_list = ([artist['name'] for artist in artists])
    artist_id_list = ([artist['id'] for artist in artists])

    currently_playing_dict = {
        "song_name": song_name,
        "song_id": song_id,
        "album_name": album_name,
        "album_id": album_id,
        "album_picture": album_picture,
        "artist_names": artist_name_list,
        "artist_ids": artist_id_list,
        "is_playing": is_playing
    }
    return currently_playing_dict


"""Retruns a List of the Images from the Spotify Artist API for the artists on the currently playing track"""
def parseArtists(artist_ids, sp):
    artist_details_json = sp.artists(artist_ids)
    artist_details_list = ([artist for artist in artist_details_json['artists']])
    artist_images_list = []
    for artist in artist_details_list:
        artist_images_list.append(artist['images'][0]['url'])
    return artist_images_list


##### Unofficial Spotify API Functions #####


"""Return the Current Time in Miliseconds"""
def currentTimeMs():
    return round(time.time() * 1000)


"""Returns a JSON Response from the Unofficial Spotify API Containing a 1 hour Access Token"""
def getUnauthAccessToken():
    # Make a request
    unofficial_api_endpoint = "https://open.spotify.com/get_access_token?reason=transport&productType=web_player"
    res = requests.get(url=unofficial_api_endpoint)
    res = res.json()
    return res


"""Use the Unofficial Spotify API To Return the Artists Cover Image"""
def getArtistHeaderImage(unauth_token, artist_id):
    endpoint_url = "https://api-partner.spotify.com/pathfinder/v1/query"
    querystring = {"operationName":"queryFullscreenMode","variables":"{\"artistUri\":\"spotify:artist:" + artist_id + "\"}","extensions":"{\"persistedQuery\":{\"version\":1,\"sha256Hash\":\"a90a0143ba80bf9d08aa03c61c86d33d214b9871b604e191d3a63cbb2767dd20\"}}"}
    headers = {
        "Authorization": "Bearer " + unauth_token,
    }
    res = requests.get(url=endpoint_url, headers=headers, params=querystring)
    res = res.json()
    return res


"""
Handles the Logic for Unauthenticated Spotify API Requests
Returns a Valid Access Token and its Expiration Time in Milliseconds
"""
def mainUnauthLogic():
    curtime_in_ms = currentTimeMs()

    # If following attributes aren't in Session Storage, go get an Unofficial Access token
    if not session.get('unofficial_access_token') or not session.get('access_token_expiration'):
        print("No Unofficial Access Token Present in Session Storage. Getting one...")
        token_request = getUnauthAccessToken()
        # Set Unofficial Access Token in Session Storage
        session['unofficial_access_token'] = token_request['accessToken']
        session['access_token_expiration'] = token_request['accessTokenExpirationTimestampMs']
        return {
            "unofficial_access_token": session.get("unofficial_access_token"),
            "access_token_expiration": session.get("access_token_expiration")
        }
    # Check if the Token has Expired
    elif (session.get('access_token_expiration') < curtime_in_ms):
        print("Unofficial Access Token Has Expired. Getting a new one...")
        token_request = getUnauthAccessToken()
        session['unofficial_access_token'] = token_request['accessToken']
        session['access_token_expiration'] = token_request['accessTokenExpirationTimestampMs']
        return {
            "unofficial_access_token": session.get("unofficial_access_token"),
            "access_token_expiration": session.get("access_token_expiration")
        }
    # We don't need an Unofficial Access Token right now
    else:
        print("We don't need an Unofficial Access token right now...")
        return {
            'unofficial_access_token': session['unofficial_access_token'],
            'access_token_expiration': session['access_token_expiration']
        }


# Running the Flask App
if __name__ == '__main__':
    app.run(host='0.0.0.0')
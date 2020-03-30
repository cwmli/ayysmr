import urllib.request
import urllib.error
import urllib.parse


reqHeaders = { "Authorization": "access_token" }

# Get a user's top tracks, we consider their top tracks
# as what the user prefers listening to in the short term
# this is the TRUTH that we want to predict
topTracksReq = urllib.request.Request(\
    "https://api.spotify.com/v1/me/top/tracks?{}".format(urllib.parse.urlencode({ "limit": 50, "time_range": "short_term" })),\
    headers=reqHeaders)

# Extract all track ids
response = urllib.request.urlopen(topTracksReq)
try:
    # Reverse mapping from artist to track
    artist2TrackMap = {}

    row = {}
    for item in response['items']:
        row[item['id']] = {
            "track": item['name'],
            "artist": item['artists'][0]['name'],
            "artist_id": item['artists'][0]['id'],
            "preview_url": item['preview_url']
        }
        artist2TrackMap[item['artists'][0]['id']] = item['id']

    # Get audio features for all top tracks
    tracksAudioFeatReq = urllib.request.Request(\
        "https://api.spotify.com/v1/audio-features?{}"\
            .format(urllib.parse.urlencode({ "ids": ",".join([*row.keys()]) })),\
        headers=reqHeaders)

    # Extract track audio features
    response = urllib.request.urlopen(tracksAudioFeatReq)
    for audioFeat in response['audio_features']:
        row[audioFeat['id']].update({
            "danceability": audioFeat['danceability'],
            "energy": audioFeat['energy'],
            "key": audioFeat['key'],
            "loudness": audioFeat['loudness'],
            "mode": audioFeat['mode'],
            "speechiness": audioFeat['speechiness'],
            "acousticness": audioFeat['acousticness'],
            "instrumentalness": audioFeat['instrumentalness'],
            "liveness": audioFeat['liveness'],
            "valence": audioFeat['valence'],
            "tempo": audioFeat['tempo']
        })

    # Get artist details for each track
    tracksAristReq = urllib.request.Request(\
        "https://api.spotify.com/v1/artists?{}"\
            .format(urllib.parse.urlencode({ "ids": ",".join([*artist2TrackMap.keys()]) })),\
        headers=reqHeaders)

    # Extract artist_id
    response = urllib.request.urlopen(tracksAristReq)
    for artist in response['artists']:
        row[artist2TrackMap[artist['id']]].update({
            "genres": artist['generes'],
            "popularity": artist['popularity']
        })
except KeyError as err:
    pass
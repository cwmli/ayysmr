import requests

from ayysmr_web.models.track import Track
from ayysmr_web.store import celery, db

@celery.task(bind = True)
def retTopTracks(self, access_token):

    reqHeaders = { "Authorization": "Bearer {}".format(access_token) }

    # Get a user's top tracks, we consider their top tracks
    # as what the user prefers listening to in the short term
    # this is the TRUTH that we want to predict
    # Extract all track ids
    response = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        params = { "limit": 50, "time_range": "short_term" },
        headers = reqHeaders
    ).json()

    # Reverse mapping from artist to track
    artist2TrackMap = {}

    row = {}
    for item in response['items']:
        row[item['id']] = {
            "name": item['name'],
            "artist": item['artists'][0]['name'],
            "artist_id": item['artists'][0]['id'],
            "preview_url": item['preview_url']
        }
        artistId = item['artists'][0]['id']
        if artistId in artist2TrackMap:
            artist2TrackMap[artistId].append(item['id'])
        else:
            artist2TrackMap[artistId] = [item['id']]

    # Get audio features for all top tracks

    # Extract track audio features
    response = requests.get(
        "https://api.spotify.com/v1/audio-features",
        params = { "ids": ",".join([*row.keys()]) },
        headers = reqHeaders
    ).json()
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

    # Extract artist_id from artist2Track mapping
    response = requests.get(
        "https://api.spotify.com/v1/artists",
        params = { "ids": ",".join([*artist2TrackMap.keys()]) },
        headers = reqHeaders
    ).json()
    for artist in response['artists']:
        
        for trackId in artist2TrackMap[artist['id']]:
            row[trackId].update({
                "genres": artist['genres'],
                "popularity": artist['popularity']
            })

    tracks = []
    # Convert to Track models and commit to db
    for k, v in row.items():
        tracks.append(Track(
            id = k,
            name = v['name'],
            artist = v['artist'],
            preview_url = v['preview_url'],
            artist_id = v['artist_id'],
            genres = v['genres'],
            popularity = v['popularity'],
            danceability = v['danceability'],
            energy = v['energy'],
            key = v['key'],
            loudness = v['loudness'],
            mode = v['mode'],
            speechiness = v['speechiness'],
            acousticness = v['acousticness'],
            instrumentalness = v['instrumentalness'],
            liveness = v['liveness'],
            valence = v['valence'],
            tempo = v['tempo']
        ))

    s = db.create_scoped_session()
    s.bulk_save_objects(tracks)
    s.commit()
    s.close()
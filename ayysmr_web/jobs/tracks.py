import requests
from datetime import datetime
from flask import current_app, url_for

from ayysmr_web.models.track import Track
from ayysmr_web.models.user import User
from ayysmr_web.store import celery, db

@celery.task
def retTopTracks(self, access_token):

    reqHeader = { "Authorization": "Bearer {}".format(access_token) }

    # Get a user's top tracks, we consider their top tracks
    # as what the user prefers listening to in the short term
    # this is the TRUTH that we want to predict
    # Extract all track ids
    response = requests.get(
        "https://api.spotify.com/v1/me/top/tracks",
        params = { "limit": 50, "time_range": "short_term" },
        headers = reqHeader
    ).json()

    tracks = extractTrackInformation(response['items'], access_token)

    s = db.create_scoped_session()
    s.bulk_save_objects(tracks)
    s.commit()
    s.close()

# TODO: Make this a periodic task
@celery.task(bind = True)
def retPlayHistory(self, start, batchsize):

    class UnauthorizedUser(requests.RequestException):
        pass

    s = db.create_scoped_session()
    users = s.query(User).limit(batchsize).offset(start).all()
    
    for user in users:
        reqHeader = { "Authorization": "Bearer {}".format(user.access_token) }

        for _retry in range(3):
            try:
                # TODO: Add paging functionality in the case where the user has listened to over 50
                # songs within the last update
                response = requests.get(
                    "https://api.spotify.com/v1/me/player/recently-played",
                    headers = reqHeader,
                    params = {
                        "limit": 50,
                        "after": int(user.last_play_history_upd.timestamp() * 1000)
                    }).json()
                # the access_token for the user is unauthorized, get the refresh token
                if 'error' in response and response['error']['status'] == 401:
                    raise UnauthorizedUser

                # otherwise we were successful dump this into Tracks
                items = map(lambda i: i['track'], response['items'])
                tracks = extractTrackInformation(items, user.access_token)

                user.last_play_history_upd = datetime.utcnow().isoformat()
                s.bulk_save_objects(tracks)
                s.commit()
                s.close()

                break

            except UnauthorizedUser:
                # Exchange refresh token for access token
                bparams = {
                    "grant_type": "refresh_token",
                    "refresh_token": user.refresh_token,
                    "redirect_uri": url_for("sy.callback", _external = True),
                    "client_id": current_app.config['SY_CLIENT_ID'],
                    "client_secret": current_app.config['SY_CLIENT_SECRET']
                }

                response = requests.post(
                    "https://accounts.spotify.com/api/token",
                    data = bparams).json()

                # Update access token and expire times
                accessToken = response['access_token']
                expireTime = response['expires_in']

                if accessToken == None:
                    return "Failed to refresh access token"

                user.access_token = accessToken
                user.expire_time = expireTime
                db.session.commit()

                continue

"""
extractTrackInformation(items)
items: an array of track objects (as specified in spotify docs)

builds a track object containing the artist details and track audio features
for each track object specified in items array
"""
def extractTrackInformation(items, access_token):
    reqHeader = { "Authorization": "Bearer {}".format(access_token) }
    # Reverse mapping from artist to track
    artist2TrackMap = {}

    row = {}
    for item in items:
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
        headers = reqHeader
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
        headers = reqHeader
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
        
    return tracks
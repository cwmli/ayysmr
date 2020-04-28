import requests
from base64 import b64encode
from datetime import datetime
from flask import current_app, url_for

from ayysmr_web.models.track import Track
from ayysmr_web.models.user import User
from ayysmr_web.store import db
from .tasks import celery

@celery.task
def retTopTracks(access_token):

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

    tracks = extractTrackInformation(response.get('items'), access_token)

    s = db.create_scoped_session()
    s.bulk_save_objects(tracks)
    s.commit()
    s.close()

@celery.task(bind = True)
def retPlayHistory(self, start, batchsize, taskcount):

    class UnauthorizedUser(requests.RequestException):
        pass

    s = db.create_scoped_session()

    index = start
    allusers = []

    while True:
        users = s.query(User).limit(batchsize).offset(index).all()

        if len(users) < 1:
            break

        for user in users:
            reqHeader = { "Authorization": "Bearer {}".format(user.access_token) }

            tracks = []
            for _retry in range(3):
                try:
                    # Paging in the case where the user has listened to over 50
                    # songs within the last update
                    time = int(user.last_play_history_upd.timestamp() * 1000)
                    while True:
                        response = requests.get(
                            "https://api.spotify.com/v1/me/player/recently-played",
                            headers = reqHeader,
                            params = {
                                "limit": 50,
                                "after": time
                            }).json()
                        # the access_token for the user is unauthorized, get the refresh token
                        if 'error' in response and response['error']['status'] == 401:
                            raise UnauthorizedUser
                        # otherwise we were successful dump this into Tracks
                        if 'items' not in response or not response['items']:
                            break

                        items = map(lambda i: i['track'], response['items'])
                        tracks = tracks + extractTrackInformation(items, user.access_token)
                        time = response['cursors']['after']

                    allusers.append(user.id)
                    # exit retry loop
                    break

                except UnauthorizedUser:
                    # Exchange refresh token for access token
                    bparams = {
                        "grant_type": "refresh_token",
                        "refresh_token": user.refresh_token,
                    }

                    response = requests.post(
                        "https://accounts.spotify.com/api/token",
                        headers = { "Authorization": 
                            "Basic " + b64encode(bytes(current_app.config['SY_CLIENT_ID'] + ":" + current_app.config['SY_CLIENT_SECRET'], "utf-8")).decode("utf-8") },
                        data = bparams).json()

                    # Update access token and expire times
                    accessToken = response.get('access_token')
                    expireTime = response.get('expires_in')

                    if response.get("error") == 'invalid_grant':
                        return "Failed to refresh access token"

                    user.access_token = accessToken
                    user.expire_time = expireTime
                    db.session.commit()

                    continue
            # commit play history and update time for the user
            user.last_play_history_upd = datetime.utcnow().isoformat()
            s.bulk_save_objects(tracks)
            s.commit()

        index = index + batchsize * taskcount
    s.close()
    return "Updated track history for {}".format(allusers)

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
            track_id = k,
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

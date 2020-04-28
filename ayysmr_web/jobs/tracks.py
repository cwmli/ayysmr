import requests
import logging
import os
from base64 import b64encode
from datetime import datetime
from flask import current_app, url_for

from ayysmr_web.models.track import Track
from ayysmr_web.models.user import User
from ayysmr_web.store import db
from .tasks import celery, taskLogger

@celery.task
def top_tracks(access_token):

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

    tracks = extract_track_information(response.get('items'), access_token)

    s = db.create_scoped_session()
    s.bulk_save_objects(tracks)
    s.commit()
    s.close()

@celery.task(bind = True)
def play_history(self, start, batchsize, taskcount):

    fh = logging.FileHandler('logs/{}'.format(self.request.id))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    taskLogger.addHandler(fh)

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
            PREVTIME = int(user.last_play_history_upd.timestamp() * 1000)

            taskLogger.debug("Updating tracks for {} last update was: {}".format(user.id, PREVTIME))

            reqHeader = { "Authorization": "Bearer {}".format(user.access_token) }

            tracks = []
            for _retry in range(3):
                try:
                    # Paging in the case where the user has listened to over 50
                    # songs within the last update
                    endtime = int(datetime.now().timestamp() * 1000)
                    while True:
                        response = requests.get(
                            "https://api.spotify.com/v1/me/player/recently-played",
                            headers = reqHeader,
                            params = {
                                "limit": 50,
                                "before": endtime
                            })

                        taskLogger.debug(response.url)

                        response = response.json()

                        # the access_token for the user is unauthorized, get the refresh token
                        if 'error' in response and response['error']['status'] == 401:
                            taskLogger.debug('Bad authorization code, attempting refresh')
                            raise UnauthorizedUser
                        # otherwise we were successful dump this into Tracks
                        if 'items' not in response or not response['items']:
                            break

                        taskLogger.debug(list(map(lambda i: (i['track']['name'], i['played_at']), response['items'])))

                        filtered = filter(lambda i: datetime.strptime(i['played_at'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp() * 1000 > PREVTIME, response['items'])

                        items = map(lambda i: i['track'], filtered)
                        tmp = extract_track_information(items, user.access_token)
                        tracks = tracks + tmp

                        endtime = response['cursors']['before']
                        
                        # exceeded
                        if int(endtime) < PREVTIME:
                            taskLogger("ending early")
                            break

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
                        data = bparams)

                    taskLogger.debug(response.url)

                    response = response.json()

                    taskLogger.debug(response)

                    # Update access token and expire times
                    accessToken = response.get('access_token')
                    expireTime = response.get('expires_in')

                    if response.get("error") == 'invalid_grant':
                        return "Failed"

                    user.access_token = accessToken
                    user.expire_time = expireTime
                    db.session.commit()

                    reqHeader = { "Authorization": "Bearer {}".format(user.access_token) }

                    taskLogger.debug('Refreshed authorization code')

                    continue

            # commit play history and update time for the user
            user.last_play_history_upd = datetime.utcnow().isoformat()
            s.bulk_save_objects(tracks)
            s.commit()

        index = index + batchsize * taskcount
    s.close()

    taskLogger.debug("Updated track history for {}".format(allusers))
    taskLogger.removeHandler(fh)

    return "Done"

"""
extract_track_information(items)
items: an array of track objects (as specified in spotify docs)

builds a track object containing the artist details and track audio features
for each track object specified in items array
"""
def extract_track_information(items, access_token):

    reqHeader = { "Authorization": "Bearer {}".format(access_token) }

    tracks = []
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

    if not row:
        return tracks

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

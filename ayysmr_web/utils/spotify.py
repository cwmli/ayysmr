import requests

from flask import url_for, current_app, flash

def get_access_token(authcode):
    # Exchange authorization code for access token
    bparams = {
        "grant_type": "authorization_code",
        "code": authcode,
        "redirect_uri": url_for("sy.callback", _external = True),
        "client_id": current_app.config['SY_CLIENT_ID'],
        "client_secret": current_app.config['SY_CLIENT_SECRET']
    }

    try:
        return requests.post(
            "https://accounts.spotify.com/api/token",
            data = bparams).json()
    except requests.HTTPError as err:
        flash("{} {}".format(err.msg, err.reason))

def get_user_profile(token):
    try:
        return requests.get(
            "https://api.spotify.com/v1/me",
            headers = { "Authorization": "Bearer {}".format(token) }).json()
    except requests.HTTPError as err:
        flash("{} {}".format(err.msg, err.reason))

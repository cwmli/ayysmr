import urllib.request
import urllib.error
import urllib.parse
import secrets
import base64

from ayysmr_web.store import db
from models.track import Track
from models.user import User

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

sy = Blueprint('sy', __name__, url_prefix='/sy')

@sy.route('/enable')
def enable():
    session['state'] = secrets.token_hex(16)
    scopes = ['user-read-recently-played', 'user-top-read']
    
    qparams = {
        "client_id": "",
        "response_type": "code",
        "redirect_uri": url_for("sy.callback"),
        "state": session['state'],
        "scope": " ".join(scopes)
    }
    
    return redirect("https://accounts.spotify.com/authorize?{}".format(urllib.parse.urlencode(qparams)))

@sy.route('/callback')
def callback():
    authcode = request.args.get('code', default = None)
    state = request.args.get('state')

    if state == session['state']:
        # Exchange authorization code for access token
        bparams = {
            "grant_type": "authorization_code",
            "code": authcode,
            "redirect_uri": url_for("sy.callback")
        }

        accessTokReq = urllib.request.Request(\
            "https://accounts.spotify.com/api/token",
            bparams,
            { "Authorization": "Basic {}".format(base64.b64encode("client_id:client_secret")) },
            method = 'POST')

        response = urllib.request.urlopen(accessTokReq)

        accessToken = response['access_token']
        expireTime = response['expires_in']
        refreshToken = response['refresh_token']

        if accessToken == None:
            flash("Failed to authorize")

        # Request associated user id
        userProfileReq = urllib.request.Request(\
            "https://api.spotify.com/v1/me",
            { "Authorization": "Bearer {}".format(accessToken) })
        userId = urllib.request.urlopen(userProfileReq)['id']

        user = User(id = userId, access_token = accessToken, refresh_token = refreshToken, expire_time = expireTime)
        db.session.add(user)
        db.session.commit()

        session['access_token'] = accessToken
        session['expire_time'] = expireTime
        session['refresh_token'] = refreshToken

    else:
        flash("Invalid state")

    return redirect(url_for('index'))

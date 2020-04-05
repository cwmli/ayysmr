import requests
import urllib.parse
import secrets
import base64

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from flask import current_app
from sqlalchemy.sql import exists

from .store import db
from .models.user import User
from .jobs.tracks import retTopTracks

sy = Blueprint('sy', __name__, url_prefix='/sy')

@sy.route('/enable')
def enable():
    session['state'] = secrets.token_hex(16)
    scopes = ['user-read-recently-played', 'user-top-read']
    
    qparams = {
        "client_id": current_app.config['SY_CLIENT_ID'],
        "response_type": "code",
        "redirect_uri": url_for("sy.callback", _external = True),
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
            "redirect_uri": url_for("sy.callback", _external = True),
            "client_id": current_app.config['SY_CLIENT_ID'],
            "client_secret": current_app.config['SY_CLIENT_SECRET']
        }

        try:
            response = requests.post(
                "https://accounts.spotify.com/api/token",
                data = bparams).json()

            accessToken = response['access_token']
            expireTime = response['expires_in']
            refreshToken = response['refresh_token']

            if accessToken == None:
                flash("Failed to authorize")

            # Request associated user id
            response = requests.get(
                "https://api.spotify.com/v1/me",
                headers = { "Authorization": "Bearer {}".format(accessToken) }).json()
            userId = response['id'] 
           
            # Add or update user tokens
            if db.session.query(exists().where(User.id == userId)).scalar() is False:
                user = User(id = userId, access_token = accessToken, refresh_token = refreshToken, expire_time = expireTime)
                db.session.add(user)
                db.session.commit()
                # trigger top tracks job for first time user
                retTopTracks.delay(accessToken)
            else:
                user = User.query.filter(User.id == userId).first()
                user.access_token = accessToken
                user.refresh_token = refreshToken
                user.expire_time = expireTime
                db.session.commit()

            session['user'] = userId
            session['access_token'] = accessToken
            session['expire_time'] = expireTime

        except requests.HTTPError as err:
            flash("{} {}".format(err.msg, err.reason))

    else:
        flash("Invalid state")

    return redirect(url_for('hello'))

@sy.route('/refresh')
def refresh():
    if not session['user']:

        user = User.query().filter(User.id == session['user']).first()

        # Exchange refresh token for access token
        bparams = {
            "grant_type": "refresh_token",
            "refresh_token": user.refresh_token,
            "redirect_uri": url_for("sy.callback"),
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
            flash("Failed to refresh access token")

        user.access_token = accessToken
        user.expire_time = expireTime
        db.session.commit()

        session['access_token'] = accessToken
        session['expire_time'] = expireTime
    else:
        flash("Invalid user session")

    return redirect(url_for('hello'))
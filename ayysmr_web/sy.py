import requests
import urllib.parse
import secrets
import base64

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, jsonify, current_app
from sqlalchemy.sql import exists

from .store import db
from .models.user import User
from .jobs.tracks import retTopTracks
from .utils import spotify

sybp = Blueprint('sy', __name__, url_prefix='/sy')

@sybp.route('/enable')
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

    rUrl = "https://accounts.spotify.com/authorize?{}".format(urllib.parse.urlencode(qparams))

    return redirect(rUrl)

@sybp.route('/callback')
def callback():
    authcode = request.args.get('code', default = None)
    state = request.args.get('state')

    if 'state' in session and state == session['state']:
        result = spotify.get_access_token(authcode)

        accessToken = result.get('access_token')
        expireTime = result.get('expires_in')
        refreshToken = result.get('refresh_token')

        if accessToken == None:
            flash("Failed to authorize", category = "error")
        else: 
            result = spotify.get_user_profile(accessToken)
            userId = result.get('id')
            
            _update_user_tokens(userId, accessToken, expireTime, refreshToken)

            session['user'] = userId
            session['access_token'] = accessToken
            session['expire_time'] = expireTime
    else:
        flash("Invalid state", category = "error")

    return redirect(url_for('hello'))

def _update_user_tokens(userid, access_token, expire_time, refresh_token):
    # Add or update user tokens
    if db.session.query(exists().where(User.id == userid)).scalar() is False:
        user = User(
            id = userid,
            access_token = access_token,
            refresh_token = refresh_token,
            expire_time = expire_time)
        db.session.add(user)
        db.session.commit()
        # trigger top tracks job for first time user
        retTopTracks.delay(access_token)
    else:
        user = User.query.filter(User.id == userid).first()
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.expire_time = expire_time
        db.session.commit()

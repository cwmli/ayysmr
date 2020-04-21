import os
import json
from unittest import mock

import pytest
import requests

from ayysmr_web.jobs import tracks
from ayysmr_web.models.track import Track
from ayysmr_web.models.user import User

class TestTrackJobs:

    def test_top_tracks_with_no_errors(self, celery):

        with open(os.path.join(os.path.dirname(__file__), 'data/test_top_tracks.txt'), 'rb') as f:
            _data_json = json.load(f)


        # Patch spotify api call with sample data
        # file contains 3 response objects for each required call
        with mock.patch("requests.Response.json") as MockedResponses:
            MockedResponses.side_effect = _data_json

            tracks.retTopTracks('token')

        # Assert that the track information is extracted and added to
        # the database
        assert Track.query.filter(Track.id == "68e6NQnd5lpCu4SPeFRNNp")
    
    def test_play_history_with_no_errors(self, celery, prep_db):

        with open(os.path.join(os.path.dirname(__file__), 'data/test_play_history.txt'), 'rb') as f:
            _data_json = json.load(f)

        # Patch spotify api call with sample data
        # file contains 4 response objects for each required call
        with mock.patch("requests.Response.json") as MockedResponses:
            MockedResponses.side_effect = _data_json

            tracks.retPlayHistory(0, 10, 1)

        # Assert that the track has been commited
        assert Track.query.filter(Track.id == "011zOYpFPsb1MLCidWlRoZ")

    def test_play_history_with_old_token(self, celery, prep_db):

        with open(os.path.join(os.path.dirname(__file__), 'data/test_play_history_with_old_token.txt'), 'rb') as f:
            _data_json = json.load(f)

        # Patch spotify api call with sample data
        # file contains 4 response objects for each required call
        with mock.patch("requests.Response.json") as MockedResponses:
            MockedResponses.side_effect = _data_json

            tracks.retPlayHistory(0, 10, 1)

        # Assert that track is represented in the database
        assert Track.query.filter(Track.id == "011zOYpFPsb1MLCidWlRoZ")
        # Assert that user tokens are now updated
        user = User.query.filter(User.id == "existingid").first()
        assert user.access_token == "newtoken"

    def test_play_history_with_failed_token(self, celery, prep_db):
      
        with open(os.path.join(os.path.dirname(__file__), 'data/test_play_history_with_failed_token.txt'), 'rb') as f:
            _data_json = json.load(f)

        # Patch spotify api call with sample data
        # file contains 3 response objects for each required call
        with mock.patch("requests.Response.json") as MockedResponses:
            MockedResponses.side_effect = _data_json

            tracks.retPlayHistory(0, 10, 1)

        # # Assert that track is represented in the database
        # assert Track.query.filter(Track.id == "011zOYpFPsb1MLCidWlRoZ")
        # Assert that user tokens are unchanged
        user = User.query.filter(User.id == "existingid").first()
        assert user.access_token == "oldtoken"
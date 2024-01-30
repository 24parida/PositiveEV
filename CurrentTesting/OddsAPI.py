import requests
import urllib
from datetime import datetime

class myException(Exception):
    pass

class API:
    def __init__(self):
        self.BASE_URL = "https://api.prop-odds.com"
        self.API_KEY = "oQK8ATTYc0ug8atzBGvgLKPOKWCaVSMOpbnWPmnE8E"
    
    def setAPI(self, api):
        self.API_KEY = api

    #### first 3 methods are adapted from prop-odds @ https://github.com/M4THYOU/prop_odds_python_example/blob/main/main.py
    def get_request(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        
        if response.status_code == 401:
            raise myException("ERROR 401")
        raise myException(f"ERROR {response.status_code}")


    def get_most_recent_odds(self, game_id, market):
        now = datetime.now()
        query_params = {
            'api_key': self.API_KEY,
            'end_date_time': now.strftime('%Y-%m-%d')
        }
        params = urllib.parse.urlencode(query_params)
        url = self.BASE_URL + '/v1/odds/' + game_id + '/' + market + '?' + params
        return self.get_request(url)
    
    def old_get_most_recent_odds(self, game_id, market):
        query_params = {
            'api_key': self.API_KEY,
        }
        params = urllib.parse.urlencode(query_params)
        url = self.BASE_URL + '/beta/odds/' + game_id + '/' + market + '?' + params
        return self.get_request(url)
    

    
    def get_fantasy_lines(self, leauge):
        now = datetime.now()
        query_params = {
            'api_key': self.API_KEY,
            'end_date_time': now.strftime('%Y-%m-%d')
        }

        params = urllib.parse.urlencode(query_params)
        url = self.BASE_URL + '/v1/fantasy_snapshot/' + leauge + '?' + params
        return self.get_request(url)

    def old_get_fantasy_lines(self, game_id, market):
        query_params = {
            'api_key': self.API_KEY,
        }

        params = urllib.parse.urlencode(query_params)
        url = self.BASE_URL + '/beta/fantasy_lines/' + game_id + '/' + market + '?' + params
        return self.get_request(url)
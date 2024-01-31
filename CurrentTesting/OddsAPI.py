import requests
import urllib
from datetime import datetime
from collections import defaultdict
import pandas as pd

class myException(Exception):
    pass

class API:
    def __init__(self):
        self.BASE_URL = "https://api.prop-odds.com"
        self.API_KEY = "oQK8ATTYc0ug8atzBGvgLKPOKWCaVSMOpbnWPmnE8E"

        self.UNDERDOG = "https://api.underdogfantasy.com/beta/v5/over_under_lines"
    
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
    
    def get_nba_games(self):
        now = datetime.now()
        query_params = {
            'date': now.strftime('%Y-%m-%d'),
            'tz': 'America/New_York',
            'api_key': self.API_KEY,
        }
        params = urllib.parse.urlencode(query_params)
        url = self.BASE_URL + '/beta/games/nba?' + params
        return self.get_request(url)


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
    

    def get_fantasy_lines(self, leauge="NBA"):

        data = requests.get(self.UNDERDOG).json()

        player_data_list2 = []
        data_dict2 = defaultdict(list)
        for i in range(0,len(data['over_under_lines'])):
            multiplier = (data['over_under_lines'][i]['options'][0]['payout_multiplier'])
            if multiplier == '1.0':
                bigname = (data['over_under_lines'][i]['over_under']['title'])
                stat = (data['over_under_lines'][i]['over_under']['appearance_stat']['display_stat'])
                #statid = (data['over_under_lines'][i]['over_under']['appearance_stat']['pickem_stat_id'])
                appearanceid = (data['over_under_lines'][i]['over_under']['appearance_stat']['appearance_id'])
                for entry in data['appearances']:
                    if entry['id'] == appearanceid:
                        playerid = entry['player_id']
                for entry in data['players']:
                    if entry['id'] == playerid:
                        sport = entry['sport_id']
                result = bigname.replace(stat, '').replace(' O/U', '').strip()

                line = (data['over_under_lines'][i]['stat_value'])

                player_data = {
                    "Name": result,
                    "League": sport,
                    "Player Props": stat,
                    "Value": line
                }
                player_data_list2.append(player_data)


        for player_info in player_data_list2:
            league = player_info["League"]
            player_name = player_info["Name"]
            prop = player_info['Player Props']
            value = player_info['Value']
            data_dict2["League"].append(league)
            data_dict2["participant_name"].append(player_name)
            data_dict2["market"].append(prop)
            data_dict2["handicap"].append(value)

        df2 = pd.DataFrame(data_dict2)
        df2 = df2[df2['League'] == leauge]


        df2 = df2[~df2['market'].str.contains("1Q")]
        df2 = df2[~df2['market'].str.contains("1H")]

        df2['market'] = df2['market'].str.replace('Double Doubles','double')
        df2['market'] = df2['market'].str.replace('3-Pointers Made','threes')
        df2['market'] = df2['market'].str.replace('+','-', regex=False)
        df2['market'] = df2['market'].str.replace(' ','')

        df2['market'] = df2['market'].str.lower()


        df2['market'] = df2['market'].str.replace('pts-rebs-asts','assists_points_rebounds')
        df2['market'] = df2['market'].str.replace('rebounds-assists','assists_rebounds')
        df2['market'] = df2['market'].str.replace('points-assists','assists_points')
        df2['market'] = df2['market'].str.replace('points-rebounds','points_rebounds')
        df2['market'] = df2['market'].str.replace('blocks-steals','blocks_steals')

        df2['market'] = 'player_' + df2['market'] + '_over_under'


        df2 = df2.drop(columns=['League'])

        df2['handicap'] = df2['handicap'].astype(float)

        return df2


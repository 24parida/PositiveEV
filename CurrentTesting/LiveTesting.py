from datetime import datetime
import pandas as pd
import sys
from tqdm import tqdm

## pivot: converts a dataframe that contains two seperate rows for each player (one for over, one for under) to have one row for each player
def pivot(df):
    pivot_df = pd.pivot_table(df, values='odds', index=['handicap', 'participant_name'], columns='name').reset_index()
    pivot_df.columns = ['line', 'participant_name', 'over_odds', 'under_odds']
    return pivot_df

## calculate odds
## adapted from Ammar Sulmanjee
def calculate_odds(x, y=None):
    if not y:
        if x>= 0: return 1 + x/100
        return 1 + 100/abs(x)
    
    ## calculate total odds
    imp_prob1 = (1 / calculate_odds(x)) * 100
    imp_prob2 = (1 / calculate_odds(y)) * 100

    ## remove VIG
    total_implied_prob = round(imp_prob1 + imp_prob2, 4)
    fair_prob1 = round(imp_prob1 / total_implied_prob * 100, 2)
    fair_prob2 = round(imp_prob2 / total_implied_prob * 100, 2)

    return [fair_prob1, fair_prob2]

## saves best bets
def download_bets(best_bets):
    ## download based on today's date
    best_bets.to_csv(f"{datetime.now().strftime('%Y-%m-%d')}_Saved_Bets.csv", index=None)


def check_participants(df):
    # Count occurrences of each participant_name
    counts = df['participant_name'].value_counts()

    # Filter participants whose name appears twice
    participants_twice = counts[counts == 2].index
    df_filtered = df[df['participant_name'].isin(participants_twice)]

    return df_filtered


# Custom API built off of Prop-Odds and Underdog API
from OddsAPI import API
api = API()

api_keys = iter([
    'FdbjrrnSeqjP1AyfWCFLm0BV9ogkykWbjxh6r9Vxe6g',
    'VnB2yYMMlbYCtRGOp5O474Lvs9zQaQLKMPY2IaQZqeY',
    'YiJ0c0wp6gi9VxrSFvT3DcDCmInwMaqyqRDfLRkMqo',
    'awY7TnqX120wfiBjqCWUpleoycTdjBBWrhBghvdY3o4',
    'qT1Y5qCKTBfyjgcgwmpeQUzhceiezzmVujciuSJOTg',
    'bcAaq0xd8KlMKfQMVreZaz6SODB2CqioZmNqNIw',
    'DIbjrARXpgFpKQF8H6uOYWSOBDwGhqj4acEeOIyYa10',
    'mcVdtfKuncfWan5DHKZ5RLglM2cwsAzPi9jX7yu8',
    'rJmjk1h96mKbZumOJDeAHQKU9FNhzrMDX8NpPOsxd1g',
    'w4jbZx8umTb0cXSe363EQT92M0zwdvNCAp3UVMNaFSc',
    'TCxSdaWzcMaTibPSqrD0XjHmWRgyE5aHWyfaTaKdPs',
    'HAzwYt7XgbqsCfiL7IJqcteMc7rdd8gqxGsKqdjGA',
    'uiAPl9kIyidxUbsiLMYdWtoo1EShhvNBxxEkrQ9j9Wg',
    'P742pehVEUpSx63Fyg73lsCLwHl4eDjCK1IemgAYzE',
    'JXs9qfuzdcvl3fqlvvQvti1ac9ft35U2L2gbArOuds'
])

## prop-odds API Key
api.setAPI(next(api_keys))

print("Started")
### Pull Underdog Lines
ud = api.get_fantasy_lines()

## Pull Prop-Odds Game's
## try each api key if error = 401 (no more calls remaining)

while True:
    try:
        games = api.get_nba_games()
        break
    except Exception as e:
        if "401" not in str(e): sys.exit()
        api.setAPI(next(api_keys))



## get markets and games for the lines
games = [i['game_id'] for i in games['games']]
markets = set(ud['market'])


## open saved bets
## if no file exists, make it an empty df
try: saved_bets = pd.read_csv(f"{datetime.now().strftime('%Y-%m-%d')}_Saved_Bets.csv")
except: saved_bets = pd.DataFrame()

## save formatted best bets, and raw data to for check_player() function
bets = pd.DataFrame()



## run though each game and each market
for game in games:
    for market in markets:
        print(game, market)
            
        # get sportsbook odds
        ## switch to next api key if ran out of uses

        while True:
            try:
                bookies_data = api.get_most_recent_odds(game, market)
                break
            except Exception as e:
                if str(e) == "ERROR 422": break
                elif "401" in str(e):
                    api.setAPI(next(api_keys))
                else: 
                    print(e)
                    break

        if len(bookies_data['sportsbooks']) <= 0: continue
             
        # format each books data     
        books = []
        for i in range(len(bookies_data['sportsbooks'])):
            df = pd.DataFrame.from_dict(bookies_data['sportsbooks'][i]['market']['outcomes'])

            ## only keep lines from today's date
            df = df[df['timestamp'].str.contains(datetime.now().strftime('%Y-%m-%d'))]

            df['book'] = bookies_data['sportsbooks'][i]['bookie_key']
            df['market'] = market
            df['name'] = df['name'].apply(lambda x: "over" if "over" in x.lower() else "under")

            books.append(df)

        # for each book, only get lines that match with underdog.
        # then conat all of these lines + odds
        new_datasets = []
        for dataset in books:
            dataset = pd.merge(dataset[['handicap', 'odds', 'participant_name', 'name', 'market']], ud, how='inner', on = ['participant_name', 'handicap' , 'market'])
            dataset = dataset[['handicap', 'odds', 'participant_name', 'name']]
            dataset = check_participants(dataset)
            
            if dataset.shape[0] > 0 and dataset.shape[1] > 0:
                # converts 2 rows (one over, one under) into 1 column for each player
                dataset = pivot(dataset)
                new_datasets.append(dataset)
        if new_datasets == []: continue

        ## concat all of these bets together
        final = pd.concat(new_datasets, axis=0)
        final = final.dropna()

        ## calculate median odds
        final[['over_odds', 'under_odds']] = final.apply(lambda row: pd.Series(calculate_odds(row['over_odds'], row['under_odds'])), axis=1)
        final = final.groupby(['participant_name', 'line']).agg({'over_odds':'median', 'under_odds':'median'}).reset_index()

        ## find ev, add market and game for each player
        final['ev'] = abs(final['over_odds'] - 50)
        final['market'] = market
        final['game'] = game


        if final.shape[0] > 0: 
            bets = pd.concat([bets, final[['participant_name', 'ev', 'market', 'line', 'over_odds', 'under_odds', 'game']]])


bets = bets.sort_values(by=['ev'], ascending=False)
bets = bets.dropna()
bets = bets.drop_duplicates(keep='first', ignore_index=True)

best_bets = bets[bets['ev'] > 4.5]

saved_bets = pd.concat([saved_bets, best_bets])

## get rid of players that already exist
saved_bets = saved_bets.drop_duplicates(subset=['participant_name', 'market', 'line'], keep='first')

download_bets(saved_bets)
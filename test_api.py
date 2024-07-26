import requests
import pandas as pd
import json
# https://api-web.nhle.com/v1/roster/VAN/20232024
# https://gitlab.com/dword4/nhlapi/-/blob/master/new-api.md
# https://github.com/Zmalski/NHL-API-Reference?tab=readme-ov-file 

# response = requests.get("http://randomfox.ca/floof")

# fox = response.json()

# print(fox['image'])



response = requests.get("https://api.nhle.com/stats/rest/en/team")

teams = response.json()['data']

df = pd.DataFrame(teams)

#Exclude these entries
start = df.loc[df['id'] == 99]
exclude = [df.loc[df['triCode'] == 'TBD'], df.loc[df['triCode'] == 'PHX']]


df = df.iloc[start.index.values[0]+1:]
df = df.drop(df.loc[df['triCode'] == 'TBD'].index.values[0])
df = df.drop(df.loc[df['triCode'] == 'PHX'].index.values[0])
df = df.reset_index()

#df.to_csv("teams.csv", index=True)
shortdf = df[['fullName', 'triCode']]
#print(shortdf)

name = df.iloc[9]['triCode']

roster_link = "https://api-web.nhle.com/v1/roster/"+name+"/20232024"

response_test = requests.get(roster_link)
van = response_test.json()
# forwards = van['forwards']
# defensemen = van['defensemen']
# goalies = van['goalies']

forwards = pd.json_normalize(van['forwards'])
defensemen = pd.json_normalize(van['defensemen'])
goalies = pd.json_normalize(van['goalies'])


columns = ['id','sweaterNumber', 'firstName.default', 'lastName.default', 'positionCode' ,'shootsCatches','heightInInches', 'weightInPounds', 'birthDate', 'birthCountry']
rename_columns = {"firstName.default":"firstName","lastName.default":"lastName"}

forwards = forwards[columns]
forwards = forwards.rename(columns=rename_columns)

defensemen = defensemen[columns]
defensemen = defensemen.rename(columns=rename_columns)

goalies = goalies[columns]
goalies = goalies.rename(columns=rename_columns)
# Index(['id', 'headshot', 'sweaterNumber', 'positionCode', 'shootsCatches',
#        'heightInInches', 'weightInPounds', 'heightInCentimeters',
#        'weightInKilograms', 'birthDate', 'birthCountry', 'firstName.default',
#        'lastName.default', 'birthCity.default', 'birthStateProvince.default',
#        'birthStateProvince.fr', 'birthStateProvince.sk',
#        'birthStateProvince.sv', 'lastName.cs', 'lastName.sk', 'birthCity.fi'],
#       dtype='object')


# print("Fowards")
# print(forwards)
# print("\nDefensemen")
# print(defensemen)
# print("\nGoalies")
# print(goalies)

# for forward in forwards:
#     print(forward['firstName']['default']+ " " + forward['lastName']['default'])

# for defenseman in defensemen:
#     print(defenseman['firstName']['default']+ " " + defenseman['lastName']['default'])

# for goalie in goalies:
#     print(goalie['firstName']['default'] + " " + goalie['lastName']['default'])


schedule_site = "https://api-web.nhle.com/v1/club-schedule-season/TOR/now"
schedule_response = requests.get(schedule_site)

convert = schedule_response.json()['games']
schedule = pd.json_normalize(convert)
#print(schedule.columns.values)

schedule = schedule[['id','homeTeam.abbrev','awayTeam.abbrev','gameDate','venueUTCOffset', 'venue.default']]
schedule = schedule.rename(columns={"homeTeam.abbrev":"home","awayTeam.abbrev":"away","venue.default":"venue", 'gameDate':'date', 'venueUTCOffset':'time'})
#print(schedule)
#schedule.to_csv("schedule.csv", index=True)




player_link = "https://api-web.nhle.com/v1/player/8480012/landing"
player_response = requests.get(player_link)
player = pd.json_normalize(player_response.json()['seasonTotals'])


# ['assists' 'gameTypeId' 'gamesPlayed' 'goals' 'leagueAbbrev' 'pim'
#  'plusMinus' 'points' 'season' 'sequence' 'teamName.default' 'avgToi'
#  'faceoffWinningPctg' 'gameWinningGoals' 'otGoals' 'powerPlayGoals'
#  'powerPlayPoints' 'shootingPctg' 'shorthandedGoals' 'shorthandedPoints'
#  'shots' 'teamName.fr']
player = player[player['gameTypeId'] == 2]
player = player[['leagueAbbrev','teamName.default','season', 'gamesPlayed','goals', 'assists','points','plusMinus']]

player = player[player['gamesPlayed'] > 10]


print(player.columns.values)
print(player)

    


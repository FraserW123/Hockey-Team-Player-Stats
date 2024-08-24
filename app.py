from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import requests
import pandas as pd

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)
    
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    franchiseId = db.Column(db.Integer, default=0)
    name = db.Column(db.String(200), nullable=False)
    tricode = db.Column(db.String(4), nullable=False)

    def __init__(self, id, franchiseId, name, tricode):
        self.id = id
        self.franchiseId = franchiseId
        self.name = name
        self.tricode = tricode

    def __repr__(self):
        return '<Team %r>' % self.id
    
def load_team(row):
    obj = Team(row['id'],row['franchiseId'], row['fullName'], row['triCode'])
    db.session.add(obj)

def load_data():
    response = requests.get("https://api.nhle.com/stats/rest/en/team")
    teams = response.json()['data']

    df = pd.DataFrame(teams)

    #Exclude these entries
    start = df.loc[df['id'] == 99]

    df = df.iloc[start.index.values[0]+1:]
    df = df.drop(df.loc[df['triCode'] == 'TBD'].index.values[0])
    df = df.drop(df.loc[df['triCode'] == 'PHX'].index.values[0])
    df = df.reset_index()

    shortdf = df[['id','franchiseId', 'fullName', 'triCode']]
    return shortdf



@app.route('/', methods=['GET'])
def index():
    # shortdf = pd.read_csv('teams.csv')[['id','franchiseId', 'fullName', 'triCode']]
    
    # shortdf = load_data()
    # shortdf.apply(load_team, axis=1)
    # db.session.commit()

    teams = Team.query.order_by(Team.id).all()
    return render_template('index.html', teams=teams)

@app.route('/roster/<int:id>', methods=['GET'])
def roster(id):
    print(id)
    team = Team.query.get_or_404(id)
    roster_link = "https://api-web.nhle.com/v1/roster/"+team.tricode+"/20232024"
    response = requests.get(roster_link)
    roster = response.json()
    forwards = pd.json_normalize(roster['forwards'])
    defensemen = pd.json_normalize(roster['defensemen'])
    goalies = pd.json_normalize(roster['goalies'])

    players = pd.concat([forwards, defensemen, goalies])

    #print(forwards.firstName.default)
    # forwards = forwards[['id','sweaterNumber', 'firstName.default', 'lastName.default', 'positionCode' ,'shootsCatches','heightInInches', 'weightInPounds', 'birthDate', 'birthCountry']]
    # forwards = forwards.rename(columns={"firstName.default":"firstName","lastName.default":"lastName","positionCode":"position","shootsCatches":"shoots","heightInInches":"height","weightInPounds":"weight","birthDate":"DOB","birthCountry":"Country"})
    
    players = players[['id','sweaterNumber', 'firstName.default', 'lastName.default', 'positionCode' ,'shootsCatches','heightInInches', 'weightInPounds', 'birthDate', 'birthCountry']]
    players = players.rename(columns={"firstName.default":"first name","lastName.default":"last name","positionCode":"position","shootsCatches":"shoots","heightInInches":"height (in)","weightInPounds":"weight (lbs)","birthDate":"DOB","birthCountry":"country", "sweaterNumber":"jersey #"})

    
    return render_template('roster.html', tables=list(players.values.tolist()), titles=players.columns.values, zip=zip)
    #return render_template('roster.html', forwards=forwards, defensemen=defensemen, goalies=goalies, team=team)

@app.route('/schedule/<int:id>', methods=['GET'])
def schedule(id):
    print(id)
    team = Team.query.get_or_404(id)
    schedule_link = "https://api-web.nhle.com/v1/club-schedule-season/"+team.tricode+"/now"
    schedule = pd.json_normalize(requests.get(schedule_link).json()['games'])

    schedule = schedule[['homeTeam.abbrev','awayTeam.abbrev','gameDate','venueUTCOffset', 'venue.default']]
    schedule = schedule.rename(columns={"homeTeam.abbrev":"home","awayTeam.abbrev":"away","venue.default":"venue", 'gameDate':'date', 'venueUTCOffset':'time (PST)'})
    return render_template('schedule.html', tables=list(schedule.values.tolist()), titles=schedule.columns.values, zip=zip)

@app.route('/player/<int:id>', methods=['GET'])
def player(id):
    print(id)

    player_link = "https://api-web.nhle.com/v1/player/"+str(id)+"/landing"
    player_response = requests.get(player_link)

    player_json = player_response.json()

    player_totals = pd.json_normalize(player_json['seasonTotals'])
    player_about = player_json['position']
    player_birthdate = player_json['birthDate']
    player_image = player_json['headshot']
    player_name = player_json['firstName']['default'] + " " + player_json['lastName']['default']
    player_number = player_json['sweaterNumber']
    print(player_about)

    print(player_json.keys())


    # ['assists' 'gameTypeId' 'gamesPlayed' 'goals' 'leagueAbbrev' 'pim'
    #  'plusMinus' 'points' 'season' 'sequence' 'teamName.default' 'avgToi'
    #  'faceoffWinningPctg' 'gameWinningGoals' 'otGoals' 'powerPlayGoals'
    #  'powerPlayPoints' 'shootingPctg' 'shorthandedGoals' 'shorthandedPoints'
    #  'shots' 'teamName.fr']

    
    player_totals = player_totals[player_totals['gameTypeId'] == 2]
    player_totals = player_totals[player_totals['gamesPlayed'] > 10]


    player_totals = player_totals.fillna(0)
    if player_about == 'G':
        print("less than 2")
        player_totals = player_totals[['leagueAbbrev','teamName.default','season', 'gamesPlayed', "goalsAgainstAvg", 'wins', 'losses', 'shutouts']]
        player_totals['goalsAgainstAvg'] = player_totals['goalsAgainstAvg'].round(2)
        
    else:
        print(player_totals['goals'].max())
        player_totals = player_totals[['leagueAbbrev','teamName.default','season', 'gamesPlayed','goals', 'assists', 'points', 'plusMinus']]
    player_totals = player_totals.rename(columns={"leagueAbbrev":"league","teamName.default":"team","season":"season","gamesPlayed":"games","plusMinus":"+/-"})

    return render_template('player.html', tables=list(player_totals.values.tolist()), titles=player_totals.columns.values, dob=player_birthdate, image=player_image, 
                           name=player_name, number=player_number, zip=zip)

@app.route('/standings', methods=['GET'])
def standings():
    standings_link = "https://api-web.nhle.com/v1/standings/now"
    standings = pd.json_normalize(requests.get(standings_link).json()['standings'])

    ['clinchIndicator' 'conferenceAbbrev' 'conferenceHomeSequence'
    'conferenceL10Sequence' 'conferenceName' 'conferenceRoadSequence'
    'conferenceSequence' 'date' 'divisionAbbrev' 'divisionHomeSequence'
    'divisionL10Sequence' 'divisionName' 'divisionRoadSequence'
    'divisionSequence' 'gameTypeId' 'gamesPlayed' 'goalDifferential'
    'goalDifferentialPctg' 'goalAgainst' 'goalFor' 'goalsForPctg'
    'homeGamesPlayed' 'homeGoalDifferential' 'homeGoalsAgainst'
    'homeGoalsFor' 'homeLosses' 'homeOtLosses' 'homePoints'
    'homeRegulationPlusOtWins' 'homeRegulationWins' 'homeTies' 'homeWins'
    'l10GamesPlayed' 'l10GoalDifferential' 'l10GoalsAgainst' 'l10GoalsFor'
    'l10Losses' 'l10OtLosses' 'l10Points' 'l10RegulationPlusOtWins'
    'l10RegulationWins' 'l10Ties' 'l10Wins' 'leagueHomeSequence'
    'leagueL10Sequence' 'leagueRoadSequence' 'leagueSequence' 'losses'
    'otLosses' 'pointPctg' 'points' 'regulationPlusOtWinPctg'
    'regulationPlusOtWins' 'regulationWinPctg' 'regulationWins'
    'roadGamesPlayed' 'roadGoalDifferential' 'roadGoalsAgainst'
    'roadGoalsFor' 'roadLosses' 'roadOtLosses' 'roadPoints'
    'roadRegulationPlusOtWins' 'roadRegulationWins' 'roadTies' 'roadWins'
    'seasonId' 'shootoutLosses' 'shootoutWins' 'streakCode' 'streakCount'
    'teamLogo' 'ties' 'waiversSequence' 'wildcardSequence' 'winPctg' 'wins'
    'placeName.default' 'teamName.default' 'teamName.fr'
    'teamCommonName.default' 'teamAbbrev.default' 'placeName.fr'
    'teamCommonName.fr']

    standings = standings[['divisionAbbrev', 'teamAbbrev.default', 'gamesPlayed', 'wins',
                           'losses', 'otLosses', 'points', 'pointPctg']]
    
    standings = standings.rename(columns={"divisionAbbrev":"division","teamAbbrev.default":"team",
                                          "gamesPlayed":"games","otLosses":"OTL", "pointPctg":"PCT"})
    
    standings = standings.round({'PCT': 3})

    metro_standings = standings[standings['division'] == 'M']
    atlantic_standings = standings[standings['division'] == 'A']
    central_standings = standings[standings['division'] == 'C']
    pacific_standings = standings[standings['division'] == 'P']

    metro_standings=metro_standings.drop(columns=['division'])
    atlantic_standings=atlantic_standings.drop(columns=['division'])
    central_standings=central_standings.drop(columns=['division'])
    pacific_standings=pacific_standings.drop(columns=['division'])

    return render_template('standings.html', tables=list(standings.values.tolist()), titles=metro_standings.columns.values, metro=list(metro_standings.values.tolist()),
                           atlantic=list(atlantic_standings.values.tolist()),central=list(central_standings.values.tolist()),pacific=list(pacific_standings.values.tolist()),zip=zip)


@app.route('/delete/<int:id>')
def delete(id):
    team_to_delete = Team.query.get_or_404(id)

    try:
        db.session.delete(team_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return "Error with deleting that task"
    
@app.route('/update/<int:id>', methods=['POST', 'GET'])
def update(id):
    team = Team.query.get_or_404(id)
    if request.method == 'POST':
        #task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except:
            return "Error with updating that task"
        
    else:
        return render_template('update.html', task = team)
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
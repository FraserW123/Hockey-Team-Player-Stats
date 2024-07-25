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
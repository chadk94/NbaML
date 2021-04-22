import nba_api as nba
import pandas as pd
import math
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import teamgamelog
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import boxscoretraditionalv2
from nba_api.stats.endpoints import playercareerstats
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Dropout
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from nba_api.stats.endpoints import commonteamroster
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonallplayers

def teamopponentstatpull(teamabb, season=2020): ##retrieve a team's entire opponent box scores over a season
    team=teams.find_team_by_abbreviation(teamabb)
    games=teamgamelog.TeamGameLog(team_id=team.get("id"),season=season)
    games=(games.get_data_frames())[0]
    gameids=games['Game_ID']
    outcome=pd.DataFrame()
    for i in range (len (gameids)):
        temp=gamestatgen(gameids[i],teamabb)
        outcome=outcome.append(temp)
    outcome=outcome.dropna()
    return outcome
def gamestatgen (gameid,teamabb): ##pull a game boxscore for the other team
    time.sleep(1)
    game=boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=gameid)
    game=(game.get_data_frames())[0]
    for i in range (game.shape[0]):
        if game["TEAM_ABBREVIATION"][i] == teamabb:
            game.drop(labels=i,axis=0,inplace=True)
    return game

def playerstatpull(player, teamabb, season=2020):  #Pull a players boxscore stats in a season for regression by name TODO automate teamabb lookup DOESNT WORK FOR ROOKIES
  players=commonallplayers.CommonAllPlayers().get_data_frames()
  players=players[0]
  listofnames=players['DISPLAY_FIRST_LAST']
  index=((list(listofnames)).index(player))
  ID= (players.loc[index,'PERSON_ID'])
  bs=playergamelog.PlayerGameLog(player_id=ID,season=season)
  df=bs.get_data_frames()
  df=df[0]
  sumplusminus=[]
  plusminus=0
  for i in range (len(df)):  ###lookupgame, sum plus minus of rest, append to list
    game=boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=df.loc[i][2])
    game=(game.get_data_frames())[0]
    for j in range (len(game)):  #TODO clean this up
        if game["TEAM_ABBREVIATION"][j]==teamabb and game["PLAYER_ID"][j]!=ID:
            if not math.isnan(game["PLUS_MINUS"][j]):    ##filters out do not play could be done better
                plusminus+=game["PLUS_MINUS"][j]
    sumplusminus.append(plusminus)
    plusminus=0
    time.sleep(1) #avoid timeout from api
  df['teamplusminus']=sumplusminus
  return df
def getplayerseasonstats(playername,playerteam,year): ##get given season stats avg for a player
    players = commonallplayers.CommonAllPlayers().get_data_frames()
    players = players[0]
    listofnames = players['DISPLAY_FIRST_LAST']
    index = ((list(listofnames)).index(playername))
    ID = (players.loc[index, 'PERSON_ID'])
    career=playercareerstats.PlayerCareerStats(player_id=ID)
    career=career.get_data_frames()
    career=career[0]
    seasonstat=career.loc[career['SEASON_ID'].str[0:4]==str(year)]
    seasonstat=seasonstat.loc[seasonstat['TEAM_ABBREVIATION']==playerteam]  ##Just in case they switch teams
    totalgames=int(seasonstat['GP'])
    seasonstat.drop(['SEASON_ID','PLAYER_ID','LEAGUE_ID','TEAM_ID','TEAM_ABBREVIATION','PLAYER_AGE','GS','GP'],axis=1,inplace=True)
    seasonstat=seasonstat.divide(totalgames)
    seasonstat['FT_PCT']=seasonstat['FT_PCT']*totalgames
    seasonstat['FG_PCT']=seasonstat['FG_PCT']*totalgames
    seasonstat['FG3_PCT']=seasonstat['FG3_PCT']*totalgames
    return seasonstat
def cleanplayerdata(playerstatdataframe): ##clean the data
    playerstatdataframe.drop(['SEASON_ID','Player_ID','Game_ID','VIDEO_AVAILABLE','GAME_DATE','MATCHUP','WL'],axis=1,inplace=True)
    return playerstatdataframe
def simplemodel():
    model=Sequential()
    model.add(Dense(20,input_dim=20,kernel_initializer='normal',activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def teamsimplemodel():
    model=Sequential()
    model.add(Dense(20,input_dim=19,kernel_initializer='normal',activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def multiplelayers():
    model=Sequential()
    model.add(Dense(20,input_dim=20,kernel_initializer='normal',activation='relu'))
    model.add(Dropout(.5))#any useless data? avoid overfitting
    model.add(Dense(10,kernel_initializer='normal',activation='relu'))
    model.add(Dropout(.5))
    model.add(Dense(5,kernel_initializer='normal',activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def teammultiplelayers():
    model=Sequential()
    model.add(Dense(20,input_dim=19,kernel_initializer='normal',activation='relu'))
    model.add(Dropout(.5))#any useless data? avoid overfitting
    model.add(Dense(10,kernel_initializer='normal',activation='relu'))
    model.add(Dropout(.5))
    model.add(Dense(5,kernel_initializer='normal',activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def widelayer():
    model = Sequential()
    model.add(Dense(40, input_dim=20, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def teamwidelayer():
    model = Sequential()
    model.add(Dense(40, input_dim=19, kernel_initializer='normal', activation='relu'))
    model.add(Dense(1,kernel_initializer='normal'))
    model.compile(loss='mean_squared_error',optimizer='adam')
    return model
def roster(team,season):
    team = teams.find_teams_by_full_name(team)
    team = team[0]
    team=commonteamroster.CommonTeamRoster(team_id=team.get("id"),season=season)
    team=(team.get_data_frames())[0]
    return team['PLAYER']
def evaluate(x,y,averages,modeltype):
    estimators=[]
    estimators.append(('standardize',StandardScaler())) #scale
    estimators.append(('mlp', KerasRegressor(build_fn=modeltype, epochs=100, batch_size=5, verbose=0)))
    pipeline=Pipeline(estimators)
    kfold = KFold(n_splits=10)
    results = cross_val_score(pipeline, x, y, cv=kfold)
    pipeline.fit(x, y)
    print("Baseline: %.2f (%.2f) MSE" % (results.mean(), results.std()))
    print("Projected +/- against a neutral opponent in a tie game is ", pipeline.predict(averages))
def evaluateteam(x, y, modeltype):
    estimators = []
    estimators.append(('standardize', StandardScaler()))  # scale
    estimators.append(('mlp', KerasRegressor(build_fn=modeltype, epochs=100, batch_size=5, verbose=0)))
    pipeline = Pipeline(estimators)
    kfold = KFold(n_splits=10)
    results = cross_val_score(pipeline, x, y, cv=kfold)
    pipeline.fit(x, y)
    leagueaverage=x.mean()
    leagueaverage=np.array(list(leagueaverage))
    leagueaverage=leagueaverage.reshape(1,-1)
    print("Baseline: %.2f (%.2f) MSE" % (results.mean(), results.std()))
    print("Projected +/- for a neutral player is ", pipeline.predict(leagueaverage))
def minconversion(stringtime): ##convert minutes to a minute decimal seconds format
    m,s=stringtime.split(':')
    return int(m)+int(s)/60
def cleanteamdata(teamdata):
    teamdata.drop(['GAME_ID','TEAM_ID','TEAM_ABBREVIATION','TEAM_CITY',"PLAYER_ID",'PLAYER_NAME','START_POSITION','COMMENT'],axis=1,inplace=True)
    teamdata['MIN']=teamdata['MIN'].map(lambda MIN: minconversion(MIN))
    return teamdata
def fullrosterprojections(teamabb,teamname,season,opponentabb,modeltype,teammodeltype):
    teamopponentprojection(teamabb,season,teammodeltype)
    teamroster = roster(teamname, season)
    for i in range (len(teamroster)):  #calculates for every player on a team
        playername=teamroster[i]
        playerdf = playerstatpull(playername, teamabb, season)
        cleaned = cleanplayerdata(playerdf)
        y = cleaned['PLUS_MINUS']
        x = cleaned.drop(['PLUS_MINUS'], axis=1)
        average = getplayerseasonstats(playername, teamabb, season)
        average['teamplusminus'] = 0
        print ("For Player: ",playername)
        evaluate(x, y, average, modeltype)
def playerprojection(playername,season,teamabb,modeltype):
    playerdf = playerstatpull(playername, teamabb, season)
    cleaned = cleanplayerdata(playerdf)
    y = cleaned['PLUS_MINUS']
    x = cleaned.drop(['PLUS_MINUS'], axis=1)
    average = getplayerseasonstats(playername, teamabb,season)
    average['teamplusminus'] = 0  ###Should this be the whole sesaon +/-
    print("variance in outcome is", np.var(y))
    evaluate(x, y, average, modeltype)
def teamopponentprojection(teamabb,season,modeltype):
    outcome = (teamopponentstatpull(teamabb, season))
    cleanteam = cleanteamdata(outcome)
    xteam = cleanteam.drop(['PLUS_MINUS'], axis=1)
    yteam = cleanteam['PLUS_MINUS']
    evaluateteam(xteam, yteam, modeltype)
playerprojection("Dennis Smith Jr.",2019,"NYK",multiplelayers)  #Hope no one here is a Knicks Fan
teamopponentprojection("BOS",2020,modeltype=teamsimplemodel)
fullrosterprojections("BOS","Celtics",2020,"MIL",multiplelayers,teammultiplelayers)
#TODO fix issues for any player with <10 games in sample. just skip over probably best choice but fails rn
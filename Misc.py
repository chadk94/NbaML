import nba_api as nba
import pandas as pd
import math
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from nba_api.stats.endpoints import boxscoretraditionalv2
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
from nba_api.stats.endpoints import playbyplayv2
from nba_api.stats.endpoints import commonteamroster

def roster(team,season):
    team = teams.find_teams_by_full_name(team)
    team = team[0]
    team=commonteamroster.CommonTeamRoster(team_id=team.get("id"),season=season)
    team=(team.get_data_frames())[0]
    return team['PLAYER']
def pullgameids(team, season): ##takes two strings for team and season returns all game ids
    team=teams.find_teams_by_full_name(team)
    team=team[0]
    gamefinder=leaguegamefinder.LeagueGameFinder(team_id_nullable=team.get("id"))
    games=(gamefinder.get_data_frames())[0]
    seasongame=games[games.SEASON_ID.str[-4:]==season]
    return seasongame['GAME_ID']
def tippull(gameid):#from game ids return tip play
        pbp=playbyplayv2.PlayByPlayV2(gameid)
        pbp=(pbp.get_data_frames())[0]
        time.sleep(1)
        if (pbp.loc[1][7]=='None'):
            return pbp.loc[1][9]
        else:
            return pbp.loc[1][7]

def firstplaypull(gameid):  # from game ids return first bucket of each
            pbp = playbyplayv2.PlayByPlayV2(gameid)
            pbp = (pbp.get_data_frames())[0]
            time.sleep(1)
            x=0
            while (pbp.loc[x][2] != 1 and pbp.loc[x][2] !=2 and pbp.loc[x][2] !=3):
                x=x+1
                if pbp.loc[x][7] is None:
                    if ("BLOCK" in pbp.loc[x][9]):
                        x=x+1
                elif pbp.loc[x][9] is None:
                    if ("BLOCK" in pbp.loc[x][7]):
                        x=x+1
            if pbp.loc[x][7] is None:
                return pbp.loc[x][9]
            else:
                return pbp.loc[x][7]
def parsetips(gameids):
    tips = []
    for i in range(len(gameids)):
        tips.append(tippull(gameids[i]))
    for i in range(len(tips)):
        if "to" in tips[i]:
            tips[i] = tips[i].split("to ", 1)[1]
    return tips
def tipcounter(tipplayers,roster):
    listroster=roster.values.tolist()
    wontip=0
    losttip=0
    for i in range(len(tipplayers)):
        if tipplayers[i] in listroster:
            wontip=wontip+1
        else:
            losttip=losttip+1
    return wontip / (wontip + losttip)
def tippercentcalc(team,year):
    teamroster = (roster(team, year))
    for i in range(len(teamroster)):
        teamroster[i] = teamroster[i].split(" ", 1)[1]
    gameids = (pullgameids(team, year))
    tipplayers = parsetips(gameids)
    ratio = tipcounter(tipplayers, teamroster)
    print("The",team," won ", ratio, "% of their tips in ",year)
def parsefirstplays(gameids):
    firstplays = []
    for i in range(len(gameids)):
        firstplays.append(firstplaypull(gameids[i]))
    for i in range(len(firstplays)):
        firstplays[i] = firstplays[i].split("(", 1)[0]
    for i in range(len(firstplays)):
        if ("MISS" in firstplays[i]):
            firstplays[i] = firstplays[i].split("MISS ")[1]
    for i in range(len(firstplays)):
        firstplays[i] = firstplays[i].split(" ", 1)[0]
    return firstplays
def countfirstshot(listofplays, roster):
    solution=[]
    listroster=roster.values.tolist()
    for i in range (len(listroster)):
        x=listofplays.count(listroster[i].split(" ")[1])
        solution.append((listroster[i],x/len(listofplays)))
    return solution
def firstshot(team,year):
    gameids=pullgameids(team, year)
    firstplays=parsefirstplays(gameids)
    teamroster=roster(team,year)
    return countfirstshot(firstplays,teamroster)

team=teams.get_teams()
teamlist=[]
for i in range (len(team)):
    teamlist.append(team[i]['full_name'])

print (tippercentcalc(teamlist[2],"2020"))
print (firstshot(teamlist[2],"2020"))


import json
from unittest.mock import patch, call

from  pystatsmpg import store as pystatsmpg
import os




def _filepath(filename):
    return os.path.join(os.path.dirname(__file__), "../../" + filename)


#Constants
csv_filename = _filepath("data/J28/Stats MPG-saison4MPG.csv")
j28_filename = _filepath("data/J28/Stats MPG-saison4MPG.xlsx")
j30_filename = _filepath("data/J30/Stats MPG-saison4MPG.xlsx")
players_json_filename = _filepath("data/players.json")
teams_json_filename = _filepath("data/teams.json")


#Setup
csv = ""


def setup_function():
    "test init function"
    global csv
    csv = _get_csv()
    pystatsmpg.clear()


#Specs
def test_get_teams_should_get_team_names():
    assert_get_teams('name')


def test_get_teams_should_get_short_names():
    assert_get_teams('short_name')


def test_get_teams_should_get_sheet():
    assert_get_teams('sheet')


def test_get_players_should_get_nom():
    assert_get_players('nom')


@patch('pystatsmpg.store._set_current_team')
def test_parseLine(mockMethod):
    for line in pystatsmpg._get_lines(csv):
        pystatsmpg._update_current_team(line)
    short_from_json = _get_json_array(teams_json_filename, 'short_name')
    assert mockMethod.call_count == len(short_from_json)
    mockMethod.assert_has_calls(map(call, short_from_json))

    
def test_extract_opposition():
    lines = csv.split('\n')
    days =  pystatsmpg._extract_opposition("Poste,Nom,Tit.,Entrée,Buts,M. L1,J01(D): TFC,J02(E ): EAG,J03(D): FCL,J04(E ): OGCN,J05(D): OL,J06(E ): SRFC,J07(D): FCN,J08(E ): SMC,J09(D): FCM,J10(E ): PSG,J11(D): FCGB,J12(E ): MHSC,J13(D): SMC,J14(E ): ASM,J15(E ): ASSE,J16(D): ASNL,J17(E ): DFCO,J18(D): LOSC,J19(E ): SCB,J20(D): ASM,J21(E ): OL,J22(D): MHSC,J23(E ): FCM,J24(D): EAG,J25(E ): FCN,J26(D): SRFC,J27(D): PSG,J28(E ): FCL,,,,,,,,,,,")
    assert len(days) == 28
    assert days[2]['day'] == 'J03'
    assert days[4]['location'] == 'D'
    assert days[4]['opponentTeam'] == 'OL'


def test_init_should_set_current_day():
    pystatsmpg.init(csv)
    assert pystatsmpg._current_day == 28


def test_clear():
    pystatsmpg.update(csv)
    teams, players = pystatsmpg.dump()
    assert len(teams.split('\n')) != ""
    pystatsmpg.clear()
    teams, players = pystatsmpg.dump()
    assert len(teams.split('\n')) > 1
    

def test_parse_note():
    assert_note_equal("2", {'entered':True, 'note':2, 'goals_neg':None})
    assert_note_equal("2:(-2)",{'entered':True, 'note':2, 'goals_pos':None, 'goals_neg':-2})
    assert_note_equal("2:2/(-4)",{'entered':True, 'note':2, 'goals_pos':2, 'goals_neg':-4})
    assert_note_equal("",{})
    assert_note_equal("<",{'entered': True})
    assert_note_equal(":2(-3)",{'entered':False, 'note':None, 'goals_pos':2, 'goals_neg':-3})


def test_days():
    pystatsmpg.update_xlsx(j28_filename)
    assert len(pystatsmpg._days) == 28
    assert pystatsmpg._days[27].with_goals == True
    pystatsmpg.update_xlsx(j30_filename)
    assert len(pystatsmpg._days) == 30
    pystatsmpg.update_xlsx(j28_filename)
    assert len(pystatsmpg._days) == 30


def test_days_with_dumps():
    pystatsmpg.update_xlsx(j28_filename)
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(players = players, teams = teams)
    assert len(pystatsmpg._days) == 28


def test_update_with_dumps():
    pystatsmpg.update(csv)
    teams, players = pystatsmpg.dump()
    assert isinstance(players, str)
    assert isinstance(teams, str)
    pystatsmpg.clear()
    pystatsmpg.update(players=players, teams=teams)
    teams_, players_ = pystatsmpg.dump()
    assert teams == teams_
    assert count_lines(players) == count_lines(players_)
    assert players == players_


def test_xlsx_to_csv():
    pystatsmpg.update_xlsx(j28_filename)
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(csv)
    t2, p2 = pystatsmpg.dump()
    assert teams == t2
    assert players == p2


def test_update_should_update_existing():
    pystatsmpg.update_xlsx(j28_filename)
    l = len(pystatsmpg._teams)
    p = pystatsmpg._players[:]
    pystatsmpg.update_xlsx(j30_filename)
    assert len(pystatsmpg._teams) == l
    
    
def test_update_should_note_remove():
    pystatsmpg.update_xlsx(j30_filename)
    assert len(pystatsmpg._teams[0].days) == 30
    assert len(pystatsmpg._players[0].note) == 30
    pystatsmpg.update_xlsx(j28_filename)
    assert len(pystatsmpg._teams[0].days) == 30
    assert len(pystatsmpg._players[0].note) == 30

    
def test_update_should_consolidate_goals():
    pystatsmpg.update_xlsx(j28_filename)
    assert len(pystatsmpg._teams[0].days) == 28
    pystatsmpg.update_xlsx(j30_filename)
    assert len(pystatsmpg._teams[0].days) == 30
    days = pystatsmpg._days
    assert days[27].with_goals == True
    assert days[29].with_goals == True
    assert [d.with_goals for d in days] == [ True if i + 1 in [28, 30] else False  for i in range(30)]


def test_with_goals_should_be_dumped():
    pystatsmpg.update_xlsx(j28_filename)
    pystatsmpg.update_xlsx(j30_filename)
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(teams=teams, players = players)
    assert_days_without_goals_except([28, 30])


def test_players_have_goals():
    pystatsmpg.update_xlsx(j28_filename)
    assert pystatsmpg._players[3].note[27].goals_pos == 1
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(teams=teams, players = players)
    assert pystatsmpg._players[3].note[27].goals_pos == 1


def test_players_remember_goals():
    pystatsmpg.update_xlsx(j28_filename)
    assert pystatsmpg._players[3].note[27].goals_pos == 1
    pystatsmpg.update_xlsx(j30_filename)
    assert pystatsmpg._players[3].note[27].goals_pos == 1
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(teams=teams, players = players)
    t2, p2 = pystatsmpg.dump()
    assert count_lines(players) == count_lines(p2)
    assert players == p2
    assert pystatsmpg._players[3].note[27].goals_pos == 1


def test_players_consolidate_goals_previous_day():
    pystatsmpg.update_xlsx(j30_filename)
    pystatsmpg.update_xlsx(j28_filename)
    assert pystatsmpg._players[3].note[27].goals_pos == 1


def test_players_consolidate_goals_previous_day_after_dump():
    pystatsmpg.update_xlsx(j30_filename)
    teams, players = pystatsmpg.dump()
    pystatsmpg.clear()
    pystatsmpg.update(teams=teams, players=players)
    pystatsmpg.update_xlsx(j28_filename)
    assert pystatsmpg._players[3].note[27].goals_pos == 1
    assert pystatsmpg._days[27].with_goals == True
    
    
#Asserts
def assert_get_teams(property):
    names_from_json = _get_json(teams_json_filename, property)
    pystatsmpg.init(csv)
    teams_from_csv = pystatsmpg._teams
    names_from_csv = extract_names(teams_from_csv, property)
    assert names_from_csv == names_from_json


def assert_get_players(property):
    names_from_json = _get_json(players_json_filename, property)
    pystatsmpg.init(csv)
    players_from_csv = pystatsmpg._players
    names_from_csv = extract_names(players_from_csv, property)
    assert names_from_csv == names_from_json


def assert_note_equal(s, values):
    note = pystatsmpg._parse_note(s)
    expe = pystatsmpg.note(**values)
    assert note.__dict__ == expe.__dict__
    

def assert_days_without_goals_except(daysindexes):
    days = pystatsmpg._days
    assert [d.with_goals for d in days] == [ True if i + 1 in daysindexes else False  for i in range(30)]

    
#Internals
def _get_json_array( file, property):
    with open(file, "r") as json_file:
        teams_from_json = json.load(json_file)
        return [team[property] for team in teams_from_json]
    

def _get_json(file, property):
    return json.dumps(_get_json_array(file, property))
    

def _get_csv():
    with open(csv_filename, "r") as csv_file:
        csv = csv_file.read()
        return csv
    


    
def extract_names_array(team_list, property='name', **keywords):
    return list(map(lambda team: getattr(team,property), team_list))


def extract_names(team_list, property='name', **keywords):
    return json.dumps(extract_names_array(team_list, property))


def count_lines(dump):
    return len(dump.split('\n'))
    
                                            

    

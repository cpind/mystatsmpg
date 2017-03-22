import json
import statsmpg

from unittest.mock import patch, call


#Constants
csv_filename = "data/Stats MPG-saison4MPG.csv"
xlsx_filename = "data/Stats MPG-saison4MPG.xlsx"
players_json_filename = "data/players.json"
teams_json_filename = "data/teams.json"


#Setup
csv = ""


def setup_function():
    "test init function"
    global csv
    csv = _get_csv()
    statsmpg.clear()


#Specs
def test_get_teams_should_get_team_names():
    assert_get_teams('name')


def test_get_teams_should_get_short_names():
    assert_get_teams('short_name')


def test_get_teams_should_get_sheet():
    assert_get_teams('sheet')


def test_get_players_should_get_nom():
    assert_get_players('nom')


@patch('statsmpg._set_current_team')
def test_parseLine(mockMethod):
    for line in statsmpg._get_lines(csv):
        statsmpg._update_current_team(line)
    short_from_json = _get_json_array(teams_json_filename, 'short_name')
    assert mockMethod.call_count == len(short_from_json)
    mockMethod.assert_has_calls(map(call, short_from_json))

    
def test_extract_opposition():
    lines = csv.split('\n')
    days =  statsmpg._extract_opposition("Poste,Nom,Tit.,Entrée,Buts,M. L1,J01(D): TFC,J02(E ): EAG,J03(D): FCL,J04(E ): OGCN,J05(D): OL,J06(E ): SRFC,J07(D): FCN,J08(E ): SMC,J09(D): FCM,J10(E ): PSG,J11(D): FCGB,J12(E ): MHSC,J13(D): SMC,J14(E ): ASM,J15(E ): ASSE,J16(D): ASNL,J17(E ): DFCO,J18(D): LOSC,J19(E ): SCB,J20(D): ASM,J21(E ): OL,J22(D): MHSC,J23(E ): FCM,J24(D): EAG,J25(E ): FCN,J26(D): SRFC,J27(D): PSG,J28(E ): FCL,,,,,,,,,,,")
    assert len(days) == 28
    assert days[2]['day'] == 'J03'
    assert days[4]['location'] == 'D'
    assert days[4]['opponentTeam'] == 'OL'


def test_init_should_set_current_day():
    statsmpg.init(csv)
    assert statsmpg._current_day == 28


def test_clear():
    statsmpg.update(csv)
    teams, players = statsmpg.dump()
    assert len(teams.split('\n')) != ""
    statsmpg.clear()
    teams, players = statsmpg.dump()
    assert len(teams.split('\n')) > 1
    

def test_update_with_dumps():
    statsmpg.update(csv)
    teams, players = statsmpg.dump()
    assert isinstance(players, str)
    assert isinstance(teams, str)
    statsmpg.clear()
    statsmpg.update(players=players, teams=teams)
    teams_, players_ = statsmpg.dump()
    assert teams == teams_
    assert count_lines(players) == count_lines(players_)
    assert players == players_


def test_xlsx_to_csv():
    statsmpg.update_xlsx(xlsx_filename)
    teams, players = statsmpg.dump()
    statsmpg.clear()
    statsmpg.update(csv)
    t2, p2 = statsmpg.dump()
    assert teams == t2
    assert players == p2

    
def test_parse_note():
    assert_note_equal("2", {'entered':True, 'note':2, 'goals_neg':None})
    assert_note_equal("2:(-2)",{'entered':True, 'note':2, 'goals_pos':None, 'goals_neg':-2})
    assert_note_equal("2:2/(-4)",{'entered':True, 'note':2, 'goals_pos':2, 'goals_neg':-4})
    assert_note_equal("",{})
    assert_note_equal("<",{'entered': True})
    assert_note_equal(":2(-3)",{'entered':False, 'note':None, 'goals_pos':2, 'goals_neg':-3})



#Asserts
def assert_get_teams(property):
    names_from_json = _get_json(teams_json_filename, property)
    statsmpg.init(csv)
    teams_from_csv = statsmpg._teams
    names_from_csv = extract_names(teams_from_csv, property)
    assert names_from_csv == names_from_json


def assert_get_players(property):
    names_from_json = _get_json(players_json_filename, property)
    statsmpg.init(csv)
    players_from_csv = statsmpg._players
    names_from_csv = extract_names(players_from_csv, property)
    assert names_from_csv == names_from_json


def assert_note_equal(s, values):
    note = statsmpg._parse_note(s)
    expe = statsmpg.note(**values)
    assert note.__dict__ == expe.__dict__
    

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
    
                                            

    

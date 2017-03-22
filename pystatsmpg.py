#here goes the Copyright (c)

"""Read mpg file stats and consolidate data"""

#Python stdlib imports
import re
import csv
import io
import argparse
import os

#uses openpyxl for reading excel 
import openpyxl


#Constants
__csv__player__columns = ['poste', 'nom', 'tit', 'entrees', 'buts', 'team']
__csv__team__columns = ['sheet', 'name', 'short_name']
_players_csv_file_ = "pystatsmpg_players.csv"
_teams_csv_file_ = "pystatsmpg_teams.csv"


#MPG constants
_entered_string = "<"
_injured_string = "Bl."


#Regex
_team_regex = r"-{8}[^0-9]*([0-9]*)[^A-Z]*([A-Z]*).*\n([^,]*)"
_day_regex = r"J[0-9]{2}"


#internals
_teams = []
_players = []
_current_team = ""
_current_day = 1
_days = []
        
def update(csv = None, players = None, teams = None):
    """update stats

    provides either the csv file OR both players and teams csv

    Keyword arguments:
    csv -- csv export of the xlsx mpg stats file
    players -- csv dumps of the stats as formatted by the dump() 
    teams -- csv dumps such as the one provided by dump()

    """
    if csv is not None:
        _update_from_csv(csv)
        return
    _update_teams(teams)
    _update_players(players)


def init(csv):
    """Init the stats with data provided as csv.  The csv layout must
    follow the layout of the xlsx file provided by mpg.  This layout
    is referred as mpg layout.

    """
    _init()
    update(csv)


def clear():
    _init()
    

def xlsx_to_csv(filename):
    wb = openpyxl.load_workbook(filename, data_only=True)
    sh = wb.get_active_sheet()
    output = io.StringIO()
    c = csv.writer(output, lineterminator="\n")
    i = 1
    for sh in wb.worksheets:
        output.write("-------- " + str(i) + " - " + sh.title + "\n")
        i = i + 1
        for r in sh.rows:
            c.writerow([cell.internal_value for cell in r])
    return output.getvalue()


def update_xlsx(xlsx):
    csv = xlsx_to_csv(xlsx)
    _update_from_csv(csv)
    

#Models    
class Team:
    """Team contains all team related properties """

    def __init__(self):
        self.sheet = ""
        self.name = ""
        self.short_name = ""
        self.days = []

        
class Note:
    """Note contains all notation related properties"""
    
    def __init__(self):
        self.note = None
        self.goals_pos = None
        self.goals_neg = None
        self.entered = False
        self.injured = False

    def __eq__(self, other):
        return self.__dict__ == other.__dict__


class Player:
    """Player contains all player related properties """

    def __init__(self):
        self.poste = ""
        self.nom = ""
        self.tit = ""
        self.entrees = ""
        self.buts = ""
        self.team = ""
        self.note = []
        self._updated = False


    def __str__(self):
        return str(self.__dict__)

        
class DayHeader:
    """Day contains all day related properties """

    def __init__(self):
        self.day = ""
        self.with_goals = False
        

        
#creators
def team(sheet, name, short_name):
    "Create a Team"
    t = Team()
    t.sheet = sheet
    t.name = name
    t.short_name = short_name
    return t


def note(
        note = None,
        goals_pos = None,
        goals_neg = None,
        entered = False,
        injured = False):
    "Create a Note"
    n = Note()
    n.note = note
    n.goals_pos = goals_pos
    n.goals_neg = goals_neg
    n.entered = entered
    n.injured = injured
    return n


def player(
        poste = "",
        nom = "",
        tit = "",
        entrees = "",
        buts = "",
        team = "",
        note = []):
    p = Player()
    p.poste = poste
    p.nom = nom
    p.tit = tit
    p.entrees = entrees
    p.buts = buts
    p.team = team
    p.note = note
    return p


def dayheader(day = "", with_goals = False):
    d = DayHeader()
    d.day = day
    d.with_goals = with_goals
    return d


#internals
def _update_players(players_csv):
    lines = players_csv.split("\n")
    _update_days_from_header_line(lines[0])
    for line in lines[1:]:
        _update_player(line.split(','))


def _update_player(player_tokens):
    "update player form the line"
    player = {}
    i = 0
    for prop in __csv__player__columns:
        player[prop] = player_tokens[i]
        i = i + 1
    p = _get_or_create_player(player)
    for prop in player:
        setattr(p, prop, player[prop])
    offset = 6
    p.note = [_parse_note(token) for token in player_tokens[offset:offset + len(_days)]]


__player_id_properties__ = ['poste', 'nom', 'team']

    
def _are_same_player(player, other):
    for prop in __player_id_properties__:
        if other[prop] != getattr(player, prop):
            return False
    return True
   
    
def _get_or_create_player(player):
    for p in _players:
        if _are_same_player(p, player):
            return p
    p = Player()
    for prop in __player_id_properties__:
        setattr(p, prop, player[prop])
    _players.append(p)
    return p
    

def _update_teams(teams_csv):
    "return array of lines skipping the header"
    lines = teams_csv.split("\n")
    for line in lines[1:]:
        _update_team(line.split(','))
    _update_days()


def _update_days():
    days = _teams[0].days
    if len(days) == 0:
        return
    if len(days) > len(_days):
        for d in range(len(_days), len(days)):
            _days.append(dayheader(days[d]['day'], False))
    #current last day always have goals
    _days[len(days)-1].with_goals = True


def _update_days_from_header_line(line):
    offset = len(__csv__player__columns)
    tokens = line.split(',')[offset:]
    days = [_parse_header_day(token) for token in tokens]
    for i in range(max(len(days), len(_days))):
        if i > len(_days):
            _days.append(days[i])
            continue
        _days[i].with_goals = days[i].with_goals
        

def _parse_header_day(token):
    d = DayHeader()
    if "*" in token:
        d.with_goals = True
        token = token[:-1]
    d.day = token
    return d


def _dump_day_header(day):
    return day.day + ("*" if day.with_goals else "")


def _get_properties(tokens, properties, columns):
    indexes = [ columns.index(prop) for prop in properties ]
    return [ tokens[i] for i in indexes ]


def _get_team_properties(tokens, properties):
    "get team properties value form csv lines token"
    return _get_properties(tokens, properties, __csv__team__columns)


def _get_or_create_team(sheet, name, short_name):
    "get or create the team"
    for t in _teams:
        if t.short_name == short_name:
            return t
    t = team(sheet, name, short_name)
    _teams.append(t)
    return t


def _update_team_days(team, days = []):
    if len(days) > len(team.days):
        team.days = days


def _update_team(team_tokens):
    "update the team from the line"
    team_properties = _get_team_properties(team_tokens, ['sheet', 'name', 'short_name'])
    t = _get_or_create_team(*team_properties)
    new_days = [_parse_day(d) for d in team_tokens[3:]]
    _update_team_days(t, new_days)


    
def _update_from_csv(csv):
    team_regex = re.compile(_team_regex, re.M)
    team_regex.sub(_team_replacer, csv)
    lines = _get_lines(csv)
    _set_current_day(lines)
    for p in _players:
        p._updated = False
    for line in lines:
        _parse_line(line)
    #removes players that have been removed
    _players[:] = [p for p in _players if p._updated]

    
def _team_replacer(match):
    sheet = int(match.group(1))
    if sheet == 1:
        return
    t = _get_or_create_team(str(sheet), match.group(3), match.group(2))

        
def _first_player_header_line(lines):
    for line in lines:
        if  _is_player_header_line(line):
            return line


def _set_current_day(lines):
    global _current_day
    line = _first_player_header_line(lines)
    days = _extract_opposition(line)
    _current_day = len(days)


def dump():
    """dump both players and teams"""
    return dump_teams(), dump_players()

    
def dump_players():
    "dump players as csv"
    columns = __csv__player__columns
    if len(_teams) > 0:
        columns = columns + [_dump_day_header(day) for day in _days]
    res = ",".join(columns) + "\n"
    return res + "\n".join([_dump_player(player) for player in _players])


def dump_teams():
    "dump teams as csv"
    columns = __csv__team__columns
    if len(_teams) > 0:
        columns = columns + [day['day'] for day in _teams[0].days]
    header = ",".join(columns)
    return header + "\n" + "\n".join([_dump_team(team) for team in _teams])


def _init():
    global _teams
    global _players
    _teams = []
    _players = []
    del _days[:]
    

def _get_lines(csv):
    lines = csv.split("\n")
    return lines[1:]


def _update_current_team(line):
    team_header_pattern = re.compile(r"-{8}")
    name_pattern = re.compile(r'[A-Z]+')
    if team_header_pattern.match(line):
        _set_current_team(name_pattern.search(line).group())


def _is_player_header_line(line):
    return line.startswith("Poste")
        

def _parse_line(line):
    _update_current_team(line)
    if _is_player_header_line(line):
        days = _extract_opposition(line)
        _current_team_set_days(days)
        _update_days()
        return
    #skip all none notation line
    if not re.match(r'^[GDMA],', line):
        return
    player = _extract_player(line)
    p = _get_or_create_player(player.__dict__)
    notescount = max(len(p.note), len(player.note))
    for i in range(notescount):
        if i + 1 > len(p.note):
            p.note.append(player.note[i])
    p.note[_current_day - 1] = player.note[_current_day - 1]
    p._updated = True

def _dump_player(player):
    "dump players as an formatted csv row"
    dump = [ getattr(player,c) for c in __csv__player__columns]
    for note in player.note:
        dump.append(_dump_note(note))
    return ",".join(dump)


def _dump_team(team):
    "csv dump team"
    dump = [getattr(team, prop) for prop in __csv__team__columns]
    for day in team.days:
        dump.append(_dump_day(day))
    return ",".join(dump)


def _dump_day(day):
    return day['day'] + " (" + day['location'] + "): " + day['opponentTeam']



def _extract_player(line):
    "extract players from an mpg csv line"
    split = line.split(',')
    p = player(**{
        'poste':split[0],
        'nom': split[1],
        'tit': split[2],
        'entrees': split[3],
        'buts': split[4],
        'team': _current_team,
        'note': _extract_notation(split[6:])
    })
    today_goals = _parse_note(":" + p.buts)
    today_note = p.note[_current_day - 1]
    _set_goals_from(today_note, today_goals)
    return p


def _set_goals_from(note, other):
    for prop in ['goals_pos', 'goals_neg']:
        setattr(note, prop, getattr(other, prop))


def _extract_notation(notes_str):
    "extract notation from an array of notes"
    notes = []
    for note_str in notes_str[:len(_days)]:
        notes.append(_parse_note(note_str))
    return notes


def _current_team_set_days(days):
    for team in _teams:
        if team.short_name != _current_team:
            continue
        _update_team_days(team, days)


def _dump_goals(note):
    goals = []
    for g in [note.goals_pos, note.goals_neg]:
        if g is  None:
            continue
        if g < 0:
            g = "(" + str(g) + ")"
        else:
            g = str(g)
        goals.append(g)
    if len(goals) == 0:
        return ""
    return "/".join(goals)


def _dump_note(note):
    res = ""
    if note.note is not None:
        res += str(note.note)
    elif note.entered:
        res += _entered_string
    elif note.injured:
        res += _injured_string
    goals = _dump_goals(note)
    if goals != "":
        res += ":" + goals
    return res


def _parse_note(note_str):
    """
    parse note such as 2, 2:4/, 2:(-1)/4, '<', 'Bl.' and so on.
    returns a Note object
    """
    note_tokens = [s.strip() for s in re.split(r'[\(\)\/:]', note_str)]
    token_note = note_tokens[0]
    note = Note()
    try:
        note.note = int(token_note)
        note.entered = True
    except ValueError:
        note.note = None
        if token_note == _entered_string:
            note.entered = True
        elif token_note == _injured_string:
            note.injured = True
    for g in note_tokens[1:]:
        if g == "":
            continue
        try:
            g = int(g)
        except ValueError:
            continue
        if g > 0:
            note.goals_pos = g
        else:
            note.goals_neg = g
    return note


def _extract_opposition(line):
    "extract days{'day', 'location', 'opponentTeam'} form a csv line"
    cells = line.split(',')
    days = []
    day_regex = re.compile(_day_regex)
    for cell in cells:
        if not day_regex.match(cell):
            continue
        d = _parse_day(cell)
        days.append(d)
    return days


def _parse_day(day_mpg):
    tokens = re.split("[:\ \(\)]", day_mpg)
    tokens = list(filter(None, tokens))
    return {
        'day':tokens[0],
        'location':tokens[1],
        'opponentTeam':tokens[2]
    }


def _set_current_team(team):
    global _current_team
    _current_team = team
        

def _read_file(filename):
    content = ""
    with open(filename, 'w+') as file:
        content = file.read()
    return content


def _write_file(filename, content):
    with open(filename, 'w') as file:
        file.seek(0)
        file.write(content)
        file.truncate()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help = "the storage dir for the data")
    parser.add_argument("input", help = "the input file, accepts xslx")
    args = parser.parse_args()
    dir = args.directory
    input = args.input
    if not os.path.isdir(dir):
        os.makedirs(dir)
    players_filepath = os.path.join(dir, _players_csv_file_)
    teams_filepath = os.path.join(dir, _teams_csv_file_)
    players = _read_file(players_filepath)
    teams = _read_file(teams_filepath)
    update(players = players, teams = teams)
    update_xlsx(input)
    _write_file(players_filepath, dump_players())
    _write_file(teams_filepath, dump_teams())

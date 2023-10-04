from mwdatabase.lol import lol_sql
from fastapi import APIRouter

router = APIRouter(
    prefix="/api/lol",
    tags=['lol']
)

# Champ v Champ solo queue stats
@router.get("/champions/matchup")
def get_champion_matchup_data(champion_ally, champion_enemy, role: str = None, region: str = None, patch: str = None, limit: int = 50, year = None, before = None, aggregate: bool = False):
    return lol_sql.get_champion_matchup_data(champion_ally, champion_enemy, role, region, patch, limit, year, before, aggregate)

# Champ specific stats
@router.get("/champions")
def get_champion_data(champion, region: str = None, limit: int = 50, aggregate: bool = False, year: str = None, before: str = None):
    return lol_sql.get_champion_data(champion, region, limit, aggregate, year, before)

# Player specific stats
@router.get("/players")
def get_player_data(playername: str, champion: str = None, limit: int = 50, patch = None, aggregate: bool = False, year: str = None, before: str = None):
    return lol_sql.get_player_data(playername, champion, limit, patch, aggregate, year, before)

# Game specific stats
# NOTE: team1 will always correspond to the queried team name, whereas team2 will always correspond to the oppenent regardless of what side the teams are playing on
# All data returned is related to team1
@router.get("/teams/games")
def get_team_games(team_name: str = "", region: str = "", limit: int = 50, aggregate: bool = False, year: str = None, before: str = None):
    return lol_sql.get_team_games(team_name, region, limit, aggregate, year, before)

# Region specific stats
@router.get("/teams/regions")
def get_team_regions(region: str = "", limit: int = 50, year: str = ""):
    return lol_sql.get_team_regions(region, limit, year)

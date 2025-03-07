import httpx
import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from typing import Any

load_dotenv()

API_KEY = os.getenv("api_key")

API_BASE_URL = "https://api.the-odds-api.com/v4/sports"
USER_AGENT = "the-odds-api/1.0"
SPORT = 'upcoming' # use the sport_key from the /sports endpoint below, or use 'upcoming' to see the next 8 games across all sports
REGIONS = 'us' # uk | us | eu | au. Multiple can be specified if comma delimited
MARKETS = 'h2h,spreads' # h2h | spreads | totals. Multiple can be specified if comma delimited
ODDS_FORMAT = 'decimal' # decimal | american
DATE_FORMAT = 'iso' # iso | unix
HEADERS = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

#mcp server
mcp = FastMCP("odds")

async def make_sports_request() -> dict[str, Any] | None:
    params = {"api_key": API_KEY}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(API_BASE_URL, headers=HEADERS, params=params, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def make_odds_request(sport: str, params: dict) -> dict[str, Any] | None:
    url = f'{API_BASE_URL}/{sport}/odds' # corrected url formatting  
    print('url:: ', url)

    async with httpx.AsyncClient() as client:
      try:
            response = await client.get(url, headers=HEADERS, params=params, timeout=30.0)
            response.raise_for_status()
            odds_json = response.json()
            print('Remaining requests', response.headers['x-requests-remaining'])
            print('Used requests', response.headers['x-requests-used'])
            return response.json()
      except Exception:
            return None

def print_formatted_odds(odds_data: list[dict]):
    """Prints the odds data in a formatted and readable way."""
    for game in odds_data:
        print(f"Game ID: {game['id']}")
        print(f"Sport: {game['sport_title']} ({game['sport_key']})")
        print(f"Commence Time: {game['commence_time']}")
        print(f"Home Team: {game['home_team']}")
        print(f"Away Team: {game['away_team']}")
        print("Bookmakers:")

        for bookmaker in game['bookmakers']:
            print(f"  {bookmaker['title']} ({bookmaker['key']}):")
            for market in bookmaker['markets']:
                print(f"    Market: {market['key']}")
                for outcome in market['outcomes']:
                    if 'point' in outcome:
                        print(f"      {outcome['name']}: Price: {outcome['price']}, Point: {outcome['point']}")
                    else:
                        print(f"      {outcome['name']}: Price: {outcome['price']}")
        print("-" * 40) # Separator between games

def format_sports_data(sports_data: dict) -> str:
    """Format sports data into a readable string."""
    return f"""
Key: {sports_data.get('key', 'Unknown')}
Group: {sports_data.get('group', 'Unknown')}
Title: {sports_data.get('title', 'Unknown')}
Description: {sports_data.get('description', 'Unknown')}
Active: {sports_data.get('active', 'Unknown')}
Has Outrights: {sports_data.get('has_outrights', 'Unknown')}
"""

def format_odds_data(odds_data: list[dict]) -> str:
    """Formats the odds data into a readable string, similar to the provided example."""
    formatted_games = []
    for game in odds_data:
        game_forecast = f"""
Sport: {game['sport_title']} ({game['sport_key']})
Home Team: {game['home_team']}
Away Team: {game['away_team']}
Commence Time: {game['commence_time']}
"""

        bookmaker_forecasts = []
        for bookmaker in game['bookmakers']:
            bookmaker_info = f"  {bookmaker['title']} ({bookmaker['key']}):"
            market_forecasts = []
            for market in bookmaker['markets']:
                market_info = f"    Market: {market['key']}"
                outcome_forecasts = []
                for outcome in market['outcomes']:
                    if 'point' in outcome:
                        outcome_info = f"      {outcome['name']}: Price: {outcome['price']}, Point: {outcome['point']}"
                    else:
                        outcome_info = f"      {outcome['name']}: Price: {outcome['price']}"
                    outcome_forecasts.append(outcome_info)
                market_forecast = f"{market_info}\n" + "\n".join(outcome_forecasts)
                market_forecasts.append(market_forecast)
            bookmaker_forecast = f"{bookmaker_info}\n" + "\n".join(market_forecasts)
            bookmaker_forecasts.append(bookmaker_forecast)

        game_forecast += "\n".join(bookmaker_forecasts)
        formatted_games.append(game_forecast)
        # print_formatted_odds(odds_data)
        print(formatted_games)

    return "\n---\n".join(formatted_games)


@mcp.tool()
async def get_in_season_sports() -> str:

    sports = await make_sports_request()

    if not sports:
        return "failed to get sports" 

    results = [format_sports_data(sport) for sport in sports]
    return "\n---\n".join(results)

@mcp.tool()
async def get_odds(sport: str, params: dict) -> str:

    odds_json = await make_odds_request(sport, params)

    if not odds_json:
        return "failed to get odds" 

    return "\n---\n".join(format_odds_data(odds_json))


import asyncio
if __name__ == "__main__":
        mcp.run(transport='stdio')
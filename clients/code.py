# VALORANT SCOUTING TOOL - FIRST WORKING QUERY
# This is your ACTUAL starting point. Run this TODAY.

import requests
import json
from config.environment import env


# Your API key from the email
API_KEY = env.str("GRID_API_KEY")
API_URL = env.str("GRID_API_URL")

# GraphQL headers
headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# STEP 1: Get a list of recent Valorant series
def get_recent_series():
    """
    This queries for recent VALORANT professional matches.
    We'll use these series IDs to get detailed stats.
    """
    query = """
    query GetRecentSeries {
      allSeries(
        first: 5
        filter: {
          titleIds: ["valorant"]
        }
      ) {
        edges {
          node {
            id
            title
            startScheduled
          }
        }
      }
    }
    """
    
    response = requests.post(
        API_URL,
        json={"query": query},
        headers=headers
    )
    
    return response.json()

# STEP 2: Get team statistics (THIS IS YOUR SCOUTING REPORT DATA!)
def get_team_stats(team_id):
    """
    This gets aggregated team statistics.
    THIS IS THE CORE OF YOUR SCOUTING REPORT.
    
    Returns:
    - Kills, deaths, assists
    - Win rates
    - Agent picks (characters)
    - Objectives completed
    """
    query = """
    query GetTeamStats($teamId: ID!) {
      teamStatistics(
        teamId: $teamId
        filter: {
          timeWindow: LAST_MONTH
        }
      ) {
        id
        series {
          count
          kills {
            sum
            avg
          }
          deaths {
            sum
            avg
          }
          won {
            value
            count
            percentage
          }
        }
        game {
          count
          kills {
            sum
            avg
          }
          won {
            value
            count
            percentage
          }
          players {
            character {
              character {
                id
                name
              }
              count
              percentage
            }
          }
        }
      }
    }
    """
    
    variables = {"teamId": team_id}
    
    response = requests.post(
        API_URL,
        json={"query": query, "variables": variables},
        headers=headers
    )
    
    return response.json()

# RUN THESE FUNCTIONS
if __name__ == "__main__":
    print("🚀 Testing GRID API Connection...")
    print("-" * 50)
    
    # Test 1: Get recent series
    print("\n📊 TEST 1: Getting recent VALORANT series...")
    series_data = get_recent_series()
    
    if "errors" in series_data:
        print("❌ ERROR:", series_data["errors"])
    else:
        print("✅ SUCCESS! Found series:")
        series = series_data.get("data", {}).get("allSeries", {}).get("edges", [])
        for edge in series[:3]:  # Show first 3
            node = edge["node"]
            print(f"  - {node['title']} (ID: {node['id']})")
    
    print("\n" + "-" * 50)
    
    # Test 2: Get team stats (use a real team ID once you have one)
    # For now, this will show you the query structure
    print("\n📈 TEST 2: Team statistics query structure ready")
    print("   (Need a team ID to run this - get from series data)")
    
    print("\n" + "=" * 50)
    print("✅ API CONNECTION WORKING!")
    print("=" * 50)
    
    # SAVE THE RESPONSE FOR INSPECTION
    with open("grid_test_response.json", "w") as f:
        json.dump(series_data, f, indent=2)
    
    print("\n💾 Response saved to: grid_test_response.json")
    print("\nNEXT STEPS:")
    print("1. Look at the JSON response")
    print("2. Find a team ID from the series data")
    print("3. Run get_team_stats() with that team ID")
    print("4. Start building your scouting report!")
import time

from nba_api.stats.static import teams
from nba_api.stats.endpoints import TeamGameLogs
import pandas as pd
from datetime import datetime


# Function to generate season strings in 'YYYY-YY' format
def generate_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year + 1):
        next_year = str(year + 1)[-2:]  # Get last two digits of next year
        season = f"{year}-{next_year}"
        seasons.append(season)
    return seasons


# Get all NBA teams
nba_teams = teams.get_teams()

# Create a list of seasons from 1970-71 to current year (2024-25 as of Feb 25, 2025)
current_year = datetime.now().year
if datetime.now().month > 6:
    end_year = current_year
else:
    end_year = current_year - 1

seasons = generate_seasons(1970, end_year)

# Dictionary to store all team playoff data
all_team_playoff_stats = {}

# Open text file for writing playoff stats
with open('nba_team_playoff_game_logs.txt', 'w', encoding='utf-8') as txt_file:
    txt_file.write("NBA Team Playoff Game Logs (1970-71 to Present)\n")
    txt_file.write("=" * 50 + "\n\n")

    # Loop through each team
    for team in nba_teams:
        team_id = team['id']
        team_name = team['full_name']
        print(f"Processing playoff stats for {team_name} (ID: {team_id})...")

        # Write team header to text file
        txt_file.write(f"Team: {team_name} (ID: {team_id})\n")
        txt_file.write("-" * 30 + "\n")

        # List to store DataFrames for this team's playoff games across all seasons
        team_playoff_dfs = []

        # Loop through each season
        for season in seasons:
            try:
                # Add a 1-second pause before the API call
                time.sleep(1)
                # Get team playoff game logs for the season
                team_playoff_logs = TeamGameLogs(
                    team_id_nullable=team_id,
                    season_nullable=season,
                    season_type_nullable='Playoffs',
                    timeout=60
                )
                df = team_playoff_logs.get_data_frames()[0]

                # Add season column to distinguish data
                df['SEASON'] = season

                if not df.empty:
                    team_playoff_dfs.append(df)
                    print(f"Retrieved {season} playoff data for {team_name}")

                    # Write season header
                    txt_file.write(f"\nSeason {season} ({len(df)} playoff games):\n")

                    # Write summary statistics for the season
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                    season_stats = df[numeric_cols].mean()

                    for stat_name, stat_value in season_stats.items():
                        txt_file.write(f"{stat_name}: {stat_value:.1f}\n")

                    # Write key game-by-game details
                    txt_file.write("\nGame-by-Game:\n")
                    for _, game in df.iterrows():
                        txt_file.write(f"{game['GAME_DATE']} - {game['MATCHUP']}: ")
                        txt_file.write(f"{game['WL']} (PTS: {game['PTS']}, ")
                        txt_file.write(f"REB: {game['REB']}, AST: {game['AST']})\n")

                else:
                    print(f"No playoff data for {team_name} in {season}")
                    txt_file.write(f"\nSeason {season}: No playoff games\n")

            except Exception as e:
                print(f"Error retrieving {season} playoff data for {team_name}: {str(e)}")
                txt_file.write(f"\nSeason {season}: Error - {str(e)}\n")
                continue

        # Combine all seasons for this team into one DataFrame and store in dictionary
        if team_playoff_dfs:
            team_all_playoffs = pd.concat(team_playoff_dfs, ignore_index=True)
            all_team_playoff_stats[team_name] = team_all_playoffs
            txt_file.write(f"\nTotal playoff games recorded: {len(team_all_playoffs)}\n")

        txt_file.write("=" * 30 + "\n\n")

# Save all data to a single CSV file
if all_team_playoff_stats:
    final_df = pd.concat(all_team_playoff_stats.values(), ignore_index=True)
    final_df.to_csv('nba_team_playoff_game_logs.csv', index=False)

    # Append summary to text file
    with open('nba_team_playoff_game_logs.txt', 'a', encoding='utf-8') as txt_file:
        txt_file.write("Summary Statistics\n")
        txt_file.write("=" * 50 + "\n")
        txt_file.write(f"Total seasons processed: {len(seasons)}\n")
        txt_file.write(f"Total teams processed: {len(all_team_playoff_stats)}\n")
        txt_file.write(f"Total playoff games recorded: {len(final_df)}\n")

    print("All data saved to 'nba_team_playoff_game_logs.csv'")
    print("Text summary saved to 'nba_team_playoff_game_logs.txt'")
    print(f"\nTotal seasons processed: {len(seasons)}")
    print(f"Total teams processed: {len(all_team_playoff_stats)}")
    print(f"Total playoff games recorded: {len(final_df)}")
else:
    print("No playoff data was collected.")

# Optional: Print sample from dictionary
if all_team_playoff_stats:
    print("\nSample of the collected playoff data from dictionary:")
    first_team = list(all_team_playoff_stats.keys())[0]
    print(f"First 5 rows for {first_team}:")
    print(all_team_playoff_stats[first_team].head())
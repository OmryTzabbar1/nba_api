from nba_api.stats.static import players
from nba_api.stats.endpoints import PlayerDashboardByYearOverYear
import pandas as pd
from datetime import datetime
import time  # Add this import for the sleep function


# Function to generate season strings in 'YYYY-YY' format
def generate_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year + 1):
        next_year = str(year + 1)[-2:]  # Get last two digits of next year
        season = f"{year}-{next_year}"
        seasons.append(season)
    return seasons


# Get all NBA players
nba_players = players.get_players()

# Create a list of seasons from 1970-71 to current year (2024-25 as of Feb 25, 2025)
current_year = datetime.now().year
if datetime.now().month > 6:
    end_year = current_year
else:
    end_year = current_year - 1

seasons = generate_seasons(1970, end_year)

# Dictionary to store all player season stats
all_player_stats = {}

# Open text file for writing player season stats
with open('nba_player_season_stats.txt', 'w', encoding='utf-8') as txt_file:
    txt_file.write("NBA Player Season Stats (Regular Season, 1970-71 to Present)\n")
    txt_file.write("=" * 50 + "\n\n")

    # Loop through each player (limiting to active players or a subset could be added)
    for player in nba_players:
        player_id = player['id']
        player_name = player['full_name']
        print(f"Processing regular season stats for {player_name} (ID: {player_id})...")

        # Write player header to text file
        txt_file.write(f"Player: {player_name} (ID: {player_id})\n")
        txt_file.write("-" * 30 + "\n")

        try:
            # Add a 2-second pause before the API call
            time.sleep(2)

            # Get player year-over-year stats for all seasons
            player_stats = PlayerDashboardByYearOverYear(
                player_id=player_id,
                season_type_playoffs='Regular Season',
                timeout=60
            )
            df = player_stats.get_data_frames()[1]  # SeasonTotalsRegularSeason

            # Filter for seasons from 1970-71 onward (though early data might be sparse)
            df['GROUP_VALUE'] = df['GROUP_VALUE'].apply(lambda x: x if '-' in x else f"{x}-{int(x) + 1:02d}")
            df = df[df['GROUP_VALUE'].isin(seasons)]

            if not df.empty:
                # Store in dictionary
                all_player_stats[player_name] = df

                # Write season-by-season data to text file
                for index, row in df.iterrows():
                    season = row['GROUP_VALUE']
                    txt_file.write(f"\nSeason {season}:\n")

                    # Write all available statistics
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                    for column in numeric_cols:
                        if column not in ['PLAYER_ID', 'RANK']:  # Skip redundant fields
                            value = row[column]
                            if pd.isna(value):
                                txt_file.write(f"{column}: N/A\n")
                            else:
                                txt_file.write(f"{column}: {value:.1f}\n")

                txt_file.write(f"\nTotal seasons recorded: {len(df)}\n")
                print(f"Retrieved data for {player_name}")
            else:
                txt_file.write("No regular season data available from 1970-71 to present\n")
                print(f"No data for {player_name} from 1970-71 onward")

        except Exception as e:
            print(f"Error retrieving data for {player_name}: {str(e)}")
            txt_file.write(f"Error retrieving data: {str(e)}\n")
            continue

        txt_file.write("=" * 30 + "\n\n")

# Save all data to a single CSV file
if all_player_stats:
    final_df = pd.concat(all_player_stats.values(), ignore_index=True)
    final_df.to_csv('nba_player_season_stats.csv', index=False)

    # Append summary to text file
    with open('nba_player_season_stats.txt', 'a', encoding='utf-8') as txt_file:
        txt_file.write("Summary Statistics\n")
        txt_file.write("=" * 50 + "\n")
        txt_file.write(f"Total seasons processed: {len(seasons)}\n")
        txt_file.write(f"Total players processed: {len(all_player_stats)}\n")
        txt_file.write(f"Total player-seasons recorded: {len(final_df)}\n")

    print("All data saved to 'nba_player_season_stats.csv'")
    print("Text summary saved to 'nba_player_season_stats.txt'")
    print(f"\nTotal seasons processed: {len(seasons)}")
    print(f"Total players processed: {len(all_player_stats)}")
    print(f"Total player-seasons recorded: {len(final_df)}")
else:
    print("No player data was collected.")

# Optional: Print sample from dictionary
if all_player_stats:
    print("\nSample of the collected player data from dictionary:")
    first_player = list(all_player_stats.keys())[0]
    print(f"First 5 rows for {first_player}:")
    print(all_player_stats[first_player].head())
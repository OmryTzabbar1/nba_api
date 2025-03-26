import time
from nba_api.stats.static import teams
from nba_api.stats.endpoints import TeamYearByYearStats
import pandas as pd
from datetime import datetime


# Function to generate season strings in 'YYYY-YY' format (for reference)
def generate_seasons(start_year, end_year):
    seasons = []
    for year in range(start_year, end_year + 1):
        next_year = str(year + 1)[-2:]  # Get last two digits of next year
        season = f"{year}-{next_year}"
        seasons.append(season)
    return seasons


# Get all NBA teams
nba_teams = teams.get_teams()

# Create a list of seasons from 1970-71 to current year (2025 as of March 13, 2025)
current_year = datetime.now().year
if datetime.now().month > 6:  # Assuming NBA season typically starts in October
    end_year = current_year
else:
    end_year = current_year - 1

seasons = generate_seasons(1970, end_year)

# Dictionary to store all team data
all_team_stats = {}

# Create a list to store detailed team data for Excel
team_detailed_data = []

# Loop through each team
for team in nba_teams:
    team_id = team['id']
    team_name = team['full_name']
    print(f"Processing {team_name} (ID: {team_id})...")

    try:
        # Add a 1-second pause before the API call
        time.sleep(1)
        # Get team year-by-year stats
        team_stats = TeamYearByYearStats(
            team_id=team_id,
            timeout=60
        )
        df = team_stats.get_data_frames()[0]

        # Filter for seasons from 1970-71 onward
        df['YEAR'] = df['YEAR'].apply(lambda x: x[:7])  # Convert '1970-71' to match our format
        df = df[df['YEAR'].isin(seasons)]

        if not df.empty:
            # Store in dictionary
            all_team_stats[team_name] = df

            # Prepare detailed data for each season
            for index, row in df.iterrows():
                season_data = {'Team': team_name, 'Team_ID': team_id, 'YEAR': row['YEAR']}
                for column in df.columns:
                    if column not in ['TEAM_ID', 'YEAR']:  # Skip redundant fields
                        season_data[column] = row[column] if not pd.isna(row[column]) else 'N/A'
                team_detailed_data.append(season_data)

            print(f"Retrieved data for {team_name}")
        else:
            print(f"No data for {team_name} from 1970-71 onward")
            # Add empty entry for teams with no data
            team_detailed_data.append({'Team': team_name, 'Team_ID': team_id, 'YEAR': 'N/A', 'GP': 'N/A'})

    except Exception as e:
        print(f"Error retrieving data for {team_name}: {str(e)}")
        # Add error entry for failed teams
        team_detailed_data.append({'Team': team_name, 'Team_ID': team_id, 'YEAR': 'Error', 'GP': str(e)})

# Convert detailed data to DataFrame
if team_detailed_data:
    final_df = pd.DataFrame(team_detailed_data)

    # Add summary statistics as a separate DataFrame
    summary_data = {
        'Metric': ['Total seasons processed', 'Total teams processed', 'Total team-seasons recorded'],
        'Value': [len(seasons), len(all_team_stats), len(final_df)]
    }
    summary_df = pd.DataFrame(summary_data)

    # Save all data to a single Excel file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"nba_team_season_totals_averages_{timestamp}.xlsx"

    # Create Excel writer object
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        # Write the main data to the 'Season_Details' sheet
        final_df.to_excel(writer, sheet_name='Season_Details', index=False, float_format='%.2f')
        # Write the summary to the 'Summary' sheet
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    print(f"All data saved to '{filename}'")
    print(f"\nTotal seasons processed: {len(seasons)}")
    print(f"Total teams processed: {len(all_team_stats)}")
    print(f"Total team-seasons recorded: {len(final_df)}")
else:
    print("No data was collected.")

# Optional: Print sample from dictionary
if all_team_stats:
    print("\nSample of the collected data from dictionary:")
    first_team = list(all_team_stats.keys())[0]
    print(f"First 5 rows for {first_team}:")
    print(all_team_stats[first_team].head())
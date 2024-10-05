import pylotoncycle
import pandas as pd
import io
from tabulate import tabulate

# Peloton credentials
username = 'username'
password = 'password' 

# Establish connection with Peloton API
conn = pylotoncycle.PylotonCycle(username, password)

# Construct the full URL for the workout history CSV
workout_history_url = f"{conn.base_url}/api/user/youruseridhere/workout_history_csv"

# Send a GET request to the URL
response = conn.s.get(workout_history_url)

# Convert the response text into a StringIO object to handle it as CSV data
csv_data = io.StringIO(response.text)

# Load the CSV data into a pandas DataFrame
df = pd.read_csv(csv_data)

# Clean column names to remove trailing/leading spaces
df.columns = df.columns.str.strip()

# Remove timezone info like (-04) from 'Workout Timestamp' and convert to datetime
df['Workout Timestamp'] = df['Workout Timestamp'].str.replace(r"\s*\(-\d+\)", "", regex=True)
df['Workout Timestamp'] = pd.to_datetime(df['Workout Timestamp'], errors='coerce')

# 1. Start Date: Capture the date of the first workout
start_date = df['Workout Timestamp'].min().date()

# Group by year and month to count the number of rides per month
df['Year-Month'] = df['Workout Timestamp'].dt.to_period('M')
monthly_workouts = df.groupby('Year-Month').size()

# Calculate when workout frequency significantly increased
pre_serious_average = monthly_workouts.iloc[:5].mean()  # Take average of first 5 months, as an example
serious_month = monthly_workouts[monthly_workouts > (2 * pre_serious_average)].index.min()

if pd.isna(serious_month):
    serious_month = "N/A"
    rides_since_serious = "N/A"
else:
    serious_date = serious_month.start_time  # Convert the serious month to a start date
    rides_since_serious = df[df['Workout Timestamp'] >= serious_date].shape[0]  # Count rides since getting serious
    serious_month = serious_month.strftime("%B %Y")

# Calculate total and average stats
total_distance = df['Distance (mi)'].sum()
average_speed = df['Avg. Speed (mph)'].mean()
total_calories = df['Calories Burned'].sum()
total_rides = df.shape[0]  # Count the number of rows, which is the number of rides

# Determine the favorite instructor
favorite_instructor = df['Instructor Name'].value_counts().idxmax() if not df['Instructor Name'].isna().all() else "N/A"

# Prepare data summary
summary_data = {
    "Total Rides": total_rides,
    "Total Distance (mi)": f"{total_distance:.2f}",
    "Average Speed (mph)": f"{average_speed:.2f}",
    "Total Calories Burned": f"{total_calories:.2f}",
    "Favorite Instructor": favorite_instructor,
    "Start Date": start_date,
    "Got Serious Around": serious_month,
    "Rides Since Getting Serious": rides_since_serious
}

# Convert summary data to a DataFrame for easier formatting with tabulate
summary_df = pd.DataFrame(list(summary_data.items()), columns=["Metric", "Value"])

# Pretty print the summary data using tabulate
print("\nWORKOUT STATISTICS SUMMARY")
print(tabulate(summary_df, headers="keys", tablefmt="fancy_grid", showindex=False))

# Optional: Additional creative formatting or display enhancements
formatted_summary = f"""
-------------------- WORKOUT SUMMARY --------------------

Total Rides                 : {total_rides}
Total Distance (mi)         : {total_distance:.2f} miles
Average Speed (mph)         : {average_speed:.2f} mph
Total Calories Burned       : {total_calories:.2f} kcal
Favorite Instructor         : {favorite_instructor}
Start Date                  : {start_date}
Got Serious Around          : {serious_month}
Rides Since Getting Serious : {rides_since_serious}

---------------------------------------------------------
"""

# Display the final formatted summary
print(formatted_summary)

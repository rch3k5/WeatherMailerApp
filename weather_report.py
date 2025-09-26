import requests
import pandas as pd
import base64
import os.path
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import date, timedelta

# Added 'gmail.readonly' to allow reading the user's profile/email address.
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

def get_gardening_weather_report():
    """
    Fetches weather data, formats it, and calculates required watering time.
    """
    report_parts = []
    try:
        latitude = 38.9870
        longitude = -94.5878
        timezone = "America/Chicago"
        
        # --- API Call for Forecast and Recent Rainfall ---
        forecast_url = "https://api.open-meteo.com/v1/forecast"
        forecast_params = {
            "latitude": latitude, "longitude": longitude, "timezone": timezone,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "past_days": 31,
            "forecast_days": 10
        }
        response = requests.get(forecast_url, params=forecast_params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data['daily'])
        df['time'] = pd.to_datetime(df['time']).dt.tz_localize(timezone)
        df.set_index('time', inplace=True)
        today = pd.Timestamp.now(tz=timezone).normalize()
        
        historical_df = df[df.index < today]
        
        rainfall_30_days = historical_df.loc[historical_df.index >= today - pd.Timedelta(days=30), 'precipitation_sum'].sum()
        rainfall_7_days  = historical_df.loc[historical_df.index >= today - pd.Timedelta(days=7), 'precipitation_sum'].sum()
        rainfall_5_days  = historical_df.loc[historical_df.index >= today - pd.Timedelta(days=5), 'precipitation_sum'].sum()
        rainfall_3_days  = historical_df.loc[historical_df.index >= today - pd.Timedelta(days=3), 'precipitation_sum'].sum()

        report_parts.append("## 🌧️ Recent Rainfall Totals")
        report_parts.append("---------------------------------")
        report_parts.append(f"Last 30 Days: {rainfall_30_days:.2f} mm (~{(rainfall_30_days / 25.4):.2f} inches)")
        report_parts.append(f"Last 7 Days:  {rainfall_7_days:.2f} mm (~{(rainfall_7_days / 25.4):.2f} inches)")
        report_parts.append(f"Last 5 Days:  {rainfall_5_days:.2f} mm (~{(rainfall_5_days / 25.4):.2f} inches)")
        report_parts.append(f"Last 3 Days:  {rainfall_3_days:.2f} mm (~{(rainfall_3_days / 25.4):.2f} inches)")
        report_parts.append("---------------------------------")

        # --- SEPARATE API Call for 10-Day Historical Soil Temperature ---
        history_url = "https://archive-api.open-meteo.com/v1/archive"
        end_date = date.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=10) # Get last 10 days
        history_params = {
            "latitude": latitude, "longitude": longitude,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "daily": "soil_temperature_0_to_7cm_mean",
            "timezone": timezone
        }
        history_response = requests.get(history_url, params=history_params)
        history_data = history_response.json()

        report_parts.append("\n## 🌱 10-Day Average Soil Temperature")
        report_parts.append("---------------------------------")
        
        if 'daily' in history_data and history_data['daily']['soil_temperature_0_to_7cm_mean']:
            hist_df = pd.DataFrame(history_data['daily'])
            soil_temp_c_series = hist_df['soil_temperature_0_to_7cm_mean'].dropna()
            
            if not soil_temp_c_series.empty:
                soil_temp_10_day_avg_c = soil_temp_c_series.mean()
                soil_temp_10_day_avg_f = (soil_temp_10_day_avg_c * 9/5) + 32
                report_parts.append(f"Average: {soil_temp_10_day_avg_f:.1f} °F")
            else:
                report_parts.append("Data not available for this period.")
        else:
            report_parts.append("Data not available for this period.")
        report_parts.append("---------------------------------\n")


        # --- Weekly Watering Calculation ---
        TARGET_WATER_PER_WEEK_INCHES = 1.0
        BASELINE_SPRINKLER_RATE_INCHES_PER_HOUR = 0.75
        PRESSURE_ADJUSTMENT_FACTOR = 1.66  # 100% + 66% increase

        adjusted_sprinkler_rate = BASELINE_SPRINKLER_RATE_INCHES_PER_HOUR * PRESSURE_ADJUSTMENT_FACTOR
        rainfall_last_7_days_inches = rainfall_7_days / 25.4
        
        water_needed_inches = TARGET_WATER_PER_WEEK_INCHES - rainfall_last_7_days_inches
        water_needed_inches = max(0, water_needed_inches)

        watering_time_minutes = 0
        if water_needed_inches > 0:
            watering_time_hours = water_needed_inches / adjusted_sprinkler_rate
            watering_time_minutes = int(watering_time_hours * 60)

        report_parts.append("## 💧 Weekly Watering Calculation")
        report_parts.append("---------------------------------")
        report_parts.append(f"Target Water Depth:      {TARGET_WATER_PER_WEEK_INCHES:.1f} inches")
        report_parts.append(f"Adjusted Sprinkler Rate: {adjusted_sprinkler_rate:.2f} inches/hour")
        report_parts.append(f"Rainfall Last 7 Days:    {rainfall_last_7_days_inches:.2f} inches")
        report_parts.append("---------------------------------")
        report_parts.append(f"This week, you need to water for approximately: {watering_time_minutes} minutes.")
        if watering_time_minutes > 0:
            report_parts.append("Recommendation: Apply this in one or two deep watering sessions.\n")
        else:
            report_parts.append("Recommendation: No watering is needed this week.\n")
        
        # --- Forecast Section (Soil Temp Removed) ---
        forecast_df = df[df.index >= today]
        report_parts.append("## ☀️ 10-Day Weather Forecast")
        report_parts.append("-----------------------------------------------------------")
        report_parts.append(f"{'Date':<15} {'High (°F)':<12} {'Low (°F)':<11} {'Rainfall (in)':<15}")
        report_parts.append("-----------------------------------------------------------")
        for forecast_date, row in forecast_df.iterrows():
            high_f = (row['temperature_2m_max'] * 9/5) + 32
            low_f = (row['temperature_2m_min'] * 9/5) + 32
            rain_in = row['precipitation_sum'] / 25.4
            day_str = forecast_date.strftime('%a, %b %d')
            report_parts.append(f"{day_str:<15} {high_f:<12.1f} {low_f:<11.1f} {rain_in:<15.2f}")
        report_parts.append("-----------------------------------------------------------\n")
        
        return "\n".join(report_parts)
        
    except Exception as e:
        return f"Error creating weather report: {e}"


def send_email(report_string):
    """
    Handles Google API authentication and sends an email.
    """
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        user_email = profile['emailAddress']

        html_body = f"<html><body><pre style='font: monospace; font-size: 14px;'>{report_string}</pre></body></html>"
        message = MIMEText(html_body, "html")

        message['to'] = user_email
        message['subject'] = 'Your Morning Gardening Weather Report'
        
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f'Message Id: {send_message["id"]}')
        print("Email sent successfully!")

    except HttpError as error:
        print(f'An error occurred: {error}')
        send_message = None

if __name__ == '__main__':
    weather_report = get_gardening_weather_report()
    if weather_report:
        send_email(weather_report)


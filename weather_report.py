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

# Added 'gmail.readonly' to allow reading the user's profile/email address.
SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.readonly']

def get_gardening_weather_report():
    """
    Fetches and displays a weather report for a specific Kansas City, MO address,
    tailored for gardening purposes.
    """
    report_parts = []
    try:
        latitude = 38.9870
        longitude = -94.5878
        timezone = "America/Chicago"
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude, "longitude": longitude, "timezone": timezone,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
            "past_days": 31,
            "forecast_days": 10
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        df = pd.DataFrame(data['daily'])
        df['time'] = pd.to_datetime(df['time']).dt.tz_localize(timezone)
        df.set_index('time', inplace=True)
        today = pd.Timestamp.now(tz=timezone).normalize()
        
        historical_df = df[df.index < today]
        
        # Replaced deprecated '.last()' with modern '.loc' filtering.
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
        report_parts.append("---------------------------------\n")

        # --- Forecast Section ---
        forecast_df = df[df.index >= today]
        
        report_parts.append("## ☀️ 10-Day Weather Forecast")
        report_parts.append("----------------------------------------------------------------")
        report_parts.append(f"{'Date':<15} {'High (°F)':<12} {'Low (°F)':<11} {'Rainfall (in)':<15}")
        report_parts.append("----------------------------------------------------------------")
        for date, row in forecast_df.iterrows():
            high_f = (row['temperature_2m_max'] * 9/5) + 32
            low_f = (row['temperature_2m_min'] * 9/5) + 32
            rain_in = row['precipitation_sum'] / 25.4
            day_str = date.strftime('%a, %b %d')
            report_parts.append(f"{day_str:<15} {high_f:<12.1f} {low_f:<11.1f} {rain_in:<15.2f}")
        report_parts.append("----------------------------------------------------------------\n")
        
        # --- Watering Advice Section ---
        report_parts.append("## 💧 Watering Advice")
        report_parts.append(" - General Rule: Most lawns need about 1 inch of water per week.")
        report_parts.append(" - Hydrangeas (Front): Poor drainage means check soil before watering.")
        report_parts.append(" - New Grass (Back): Low sun means it holds moisture; avoid overwatering.")
        
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

        # Use <pre> tag for pre-formatted text to preserve spacing in email
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

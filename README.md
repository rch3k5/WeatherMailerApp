Automated Gardening Weather Report Mailer
This project is a fully automated Python script that fetches and processes historical and forecasted weather data for a specific location, formats it into a user-friendly report, and sends it as an email at a scheduled time. The primary goal is to provide actionable insights for gardening decisions, such as when to water plants based on recent rainfall and upcoming weather conditions.

The entire process is automated using GitHub Actions, running on a CRON schedule to deliver the report via the Gmail API every Monday, Wednesday, and Friday at 5:00 AM.

Key Features
Custom Weather Data: Fetches historical rainfall data for the last 3, 5, 7, and 30 days.

10-Day Forecast: Provides a detailed 10-day forecast including temperature highs, lows, and expected precipitation.

Tailored Advice: Includes specific, hard-coded gardening advice based on the data.

Automated Email Delivery: Sends the formatted report as a clean, pre-formatted HTML email.

Serverless Automation: Uses GitHub Actions for reliable, serverless, and scheduled execution without needing a dedicated server.

Secure Authentication: Leverages the official Google API Client Library with OAuth 2.0 to securely interact with the Gmail API, storing credentials safely in encrypted GitHub Secrets.

Technologies Used
Language: Python

Libraries:

requests: For making HTTP requests to the weather API.

pandas: For efficient data manipulation and time-series analysis.

google-api-python-client, google-auth-oauthlib: For securely authenticating with and using Google's APIs.

APIs:

Open-Meteo API: For providing free, high-quality global weather data without an API key.

Gmail API: For sending emails from a secure, modern API endpoint.

Automation & CI/CD:

GitHub Actions: To schedule and run the Python script automatically.

Cloud Services:

Google Cloud Platform: To manage API access and OAuth 2.0 credentials for the project.

How It Works
The automation is handled entirely by a GitHub Actions workflow defined in .github/workflows/mailer.yml.

Scheduled Trigger: A CRON job triggers the workflow at 5:00 AM (CDT) every Monday, Wednesday, and Friday. It can also be triggered manually.

Secure Credential Loading: The workflow runner checks out the repository code and securely loads the Google API credentials, which are stored as Base64-encoded strings in encrypted GitHub Secrets. These secrets are decoded and written to the necessary credentials.json and token.json files at runtime.

Script Execution: The Python script (weather_report.py) runs and performs the following tasks:

Calls the Open-Meteo API to get weather data for the specified GPS coordinates.

Uses Pandas to process the JSON response, calculate historical rainfall totals, and format the forecast.

Constructs a formatted string containing the full report.

Authenticates with the Gmail API using the restored token.json and credentials.json files.

Sends the report as an HTML-formatted email to the authenticated user.

Security Measures
Security was a top priority for this project to ensure that sensitive API credentials and tokens were never exposed.

.gitignore: The repository is configured with a .gitignore file to explicitly prevent credentials.json and token.json from ever being committed.

GitHub Secrets: All sensitive data is stored in encrypted GitHub Secrets, not in plaintext files within the repository.

Base64 Encoding: As an additional layer of reliability and to prevent formatting issues, the JSON credential files are stored as Base64-encoded strings. The workflow decodes them just before the script runs.

OAuth 2.0: The project uses the industry-standard OAuth 2.0 protocol to grant the script permission to send emails, which is more secure than using less secure app passwords.

Setup for a Similar Project
To replicate this project, you would need to:

Set up a project in the Google Cloud Console, enable the Gmail API, and download credentials.json for a Desktop App.

Run the script once locally to complete the OAuth 2.0 flow and generate the token.json file.

Create a new public GitHub repository with a .gitignore file.

Encode both credentials.json and token.json into Base64 strings.

Add the encoded strings as CREDENTIALS_JSON and TOKEN_JSON secrets in the repository settings.

Commit the Python script and the .github/workflows/mailer.yml workflow file.

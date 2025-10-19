# ===================================================================
#  Google OAuth Token Refresh Script
#  This script automates the process of generating a new token.json
#  and converting it to Base64 for GitHub Actions.
# ===================================================================

# --- Configuration ---
$tokenFile = "token.json"
$pythonScript = "weather_report.py"

# --- Step 1: Clean up the old token file ---
Write-Host "--- Step 1: Checking for old token file... ---" -ForegroundColor Green

if (Test-Path $tokenFile) {
    Write-Host "Found old '$tokenFile'. Deleting it now." -ForegroundColor Yellow
    Remove-Item $tokenFile
} else {
    Write-Host "No old '$tokenFile' found. Ready to create a new one."
}
Write-Host "`n" # Add a blank line for spacing

# --- Step 2: Run the Python script to get a new token ---
Write-Host "--- Step 2: Starting the authorization process... ---" -ForegroundColor Green
Write-Host "Your browser will now open. Please sign in to your Google Account"
Write-Host "and grant the application permission. Leave this window open."
Write-Host "----------------------------------------------------------------"

# This command runs the python script and waits for it to complete.
python $pythonScript

Write-Host "----------------------------------------------------------------"
Write-Host "Authorization process complete."
Write-Host "`n"

# --- Step 3: Convert the new token to Base64 ---
Write-Host "--- Step 3: Converting new token for GitHub... ---" -ForegroundColor Green

if (Test-Path $tokenFile) {
    # Read the new token file and convert it to a Base64 string
    $base64String = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tokenFile))
    
    # Copy the Base64 string directly to the clipboard
    Set-Clipboard -Value $base64String
    
    Write-Host "SUCCESS: The new Base64 token has been copied to your clipboard!" -ForegroundColor Green
    Write-Host "You can now paste this directly into the TOKEN_JSON secret on GitHub."
} else {
    Write-Host "ERROR: A new '$tokenFile' was not created." -ForegroundColor Red
    Write-Host "The authorization may have failed or been cancelled in the browser."
}

Write-Host "`n"
Read-Host -Prompt "Press Enter to exit"
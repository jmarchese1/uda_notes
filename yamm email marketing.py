import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import requests  # Used to trigger the Apps Script web app
from google_auth_oauthlib.flow import InstalledAppFlow

# -------------------------------
# 🔹 Step 1: Load BuiltWith CSV & Extract Next Batch of Emails
# -------------------------------
df = pd.read_csv(r"C:\Users\jason\Downloads\Dummy_Email_List.csv")  # Replace with actual CSV path
df
# Ensure processed_emails.csv exists; if not, create an empty one.
try:
    processed_emails = set(pd.read_csv("processed_emails.csv")["Email"])
except FileNotFoundError:
    processed_emails = set()
    pd.DataFrame(columns=["Email"]).to_csv("processed_emails.csv", index=False)
    
# Remove already processed emails and select the next batch (for testing using a small batch, here 3 emails)
df = df[~df["Email"].isin(processed_emails)]
df_batch = df.head(3)  # Change to 1500 when ready

# -------------------------------
# 🔹 Step 2: Authenticate & Upload to Google Sheets for YAMM
# -------------------------------
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
flow = InstalledAppFlow.from_client_secrets_file(r"C:\Users\jason\Downloads\oauth_credentials.json", scopes=scope)
creds = flow.run_local_server(port=0)  # Opens browser for authentication
client = gspread.authorize(creds)
sheet = client.open("YAMM Email Tracking").sheet1

# Clear sheet and upload new batch
sheet.clear()
sheet.append_row(["Website", "Email", "Company Name", "EMAIL STATUS", "LAST OPEN DATE", "LAST REPLY DATE"])
sheet.append_rows(df_batch.values.tolist())

# Append these emails to processed_emails.csv to avoid duplicates in the future
df_batch.to_csv("C:/Users/jason/Downloads/processed_emails.csv", mode='a', index=False, header=False)
print(f"✅ Uploaded {len(df_batch)} emails to YAMM Google Sheet!")

# -------------------------------
# 🔹 Step 2.5: Trigger YAMM Email Sending Automatically
# -------------------------------
# Replace <YOUR_WEB_APP_URL> with your published Google Apps Script URL.
web_app_url = "https://script.google.com/macros/s/AKfycbx219hwdv-1phvvZAVbudBd_TeHw9GymQZydbETuZaunDcUxmW0WI9y3dKc4ivfwHHN/exec"
try:
    response = requests.get(web_app_url)
    if response.status_code == 200:
        print("✅ Successfully triggered YAMM email sending via Google Apps Script!")
    else:
        print(f"❌ Failed to trigger email sending. Status code: {response.status_code}")
except Exception as e:
    print(f"❌ Exception occurred while triggering email sending: {e}")

# -------------------------------
# 🔹 Step 3: Wait & Fetch Email Results from YAMM
# -------------------------------
# Wait 24 hours (86400 seconds) to allow YAMM to process and update the tracking sheet
time.sleep(86400)
sheet_data = sheet.get_all_records()
df_results = pd.DataFrame(sheet_data)
df_results
# Merge YAMM results back into the original dataset (if needed)
df = df.merge(df_results[['Email', 'EMAIL STATUS', 'LAST OPEN DATE', 'LAST REPLY DATE']], 
              on="Email", how="left")

df
df.to_csv("updated_email_tracking.csv", index=False)
print("✅ YAMM email results pulled into DataFrame")

# -------------------------------
# 🔹 Step 4: Send Follow-Ups to Non-Responders via SMTP
# -------------------------------
GMAIL_USER = "jason@botleadgen.com"  # Replace with your Gmail address (or custom domain)
GMAIL_PASSWORD = "jfpn elef uvmy gbjd"  # Use a secure app password

def send_followup(to_email, company_name):
    subject = f"Still Interested in AI Chatbots for {company_name}?"
    body = f"""
    Hi,

    I noticed you opened my previous email but didn’t reply.
    Would you be interested in learning how AI chatbots can increase sales?

    Let me know if you’d like a quick chat!

    Best,
    [Your Name]
    """
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
    print(f"✅ Follow-up sent to {to_email}")

# Loop through results and send follow-ups to non-responders
for _, row in df.iterrows():
    if row["EMAIL STATUS"] == "Opened" and row["LAST REPLY DATE"] == "":
        send_followup(row["Email"], row["Company Name"])
        time.sleep(2)  # Short pause to prevent spam flags

# -------------------------------
# 🔹 Step 5: Automate Daily Execution
# -------------------------------
print("✅ All tasks completed. Next batch will run in 24 hours.")
time.sleep(86400)  # Wait 24 hours before running the process again

send_followup("dnichol2@nd.edu", "Dimo")

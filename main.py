from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import base64
import re
from email.mime.text import MIMEText
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

# 🔑 Groq API Key
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify', 
    'https://www.googleapis.com/auth/calendar' ] 


# 🔐 Gmail Authentication
def authenticate():
    creds = None
    if os.path.exists('token.json'):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

# 🧠 Helper: Get Full Email Body
def get_email_body(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
    else:
        data = payload['body'].get('data')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')
    return body
# -----------------------------------------
# Naya Logout Function
# -----------------------------------------
def logout():
    if os.path.exists('token.json'):
        os.remove('token.json')
        return True
    return False

# -----------------------------------------
# Updated Reply Generator (Strictly Only Body)
# -----------------------------------------
def generate_reply(email_text):
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You are a professional email assistant. Write ONLY the exact email body that needs to be sent. Do NOT include 'Subject:', 'Summary:', greetings placeholders, or any introductory/concluding remarks. Start directly with the message."},
            {"role": "user", "content": f"Write a professional reply for this email:\n{email_text}"}
        ]
    )
    return response.choices[0].message.content.strip()

# -----------------------------------------
# Updated Classifier (Using SAME Model)
# -----------------------------------------
def classify_email(email_text):
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192", 
            messages=[
                {"role": "system", "content": "You are an email classifier. Read the email and strictly reply with ONLY ONE of these words: 'Spam', 'Priority', or 'Normal'."},
                {"role": "user", "content": f"Email text: {email_text[:1000]}"}
            ]
        )
        category = response.choices[0].message.content.strip().title()
        if category not in ["Spam", "Priority", "Normal"]:
            return "Normal"
        return category
    except Exception as e:
        print(f"Classification Error: {e}")
        return "Normal"
# # ✍️ Generate Reply
# def generate_reply(email_text):
#     response = client.chat.completions.create(
#         model="llama-3.1-8b-instant",
#         messages=[
#             {"role": "system", "content": "You are a professional email assistant."},
#             {"role": "user", "content": f"Write a professional reply for this email:\n{email_text}"}
#         ]
#     )
#     return response.choices[0].message.content

# # 🧩 AI-Powered Email Classification (Upgraded)
# def classify_email(email_text):
#     try:
#         response = client.chat.completions.create(
#             model="llama-3.1-8b-instant", # Fast model for quick classification
#             messages=[
#                 {"role": "system", "content": "You are an email classifier. Read the email and strictly reply with ONLY ONE of these words: 'Spam', 'Priority', or 'Normal'."},
#                 {"role": "user", "content": f"Email text: {email_text[:1000]}"} # Limiting text length for safety
#             ]
#         )
#         category = response.choices[0].message.content.strip().title()
        
#         # Fallback if AI gives weird output
#         if category not in ["Spam", "Priority", "Normal"]:
#             return "Normal"
#         return category
#     except Exception as e:
#         print(f"Classification Error: {e}")
#         return "Normal"

# 📤 Send Email
def send_email(service, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'raw': raw}
    service.users().messages().send(userId='me', body=body).execute()

# 💾 Save Draft
def save_draft(service, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    body = {'message': {'raw': raw}}
    service.users().drafts().create(userId='me', body=body).execute()

# 📩 Read + Process Emails (Upgraded with Sender ID and Full Body)
def read_emails(service):
    results = service.users().messages().list(userId='me', maxResults=5).execute()
    messages = results.get('messages', [])

    print("\n📩 Processing Emails:\n")

    for msg in messages:
        # format='full' use kiya taaki poora email aur headers mil sakein
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data.get('payload', {})
        headers = payload.get('headers', [])

        sender = "Unknown Sender"
        subject = "No Subject"

        # Headers se Sender aur Subject extract karna
        for header in headers:
            if header['name'].lower() == 'from':
                sender = header['value']
            elif header['name'].lower() == 'subject':
                subject = header['value']

        # Poora email body extract karna
        email_text = get_email_body(payload)
        if not email_text:
            email_text = msg_data.get('snippet', '')

        # AI Classification
        category = classify_email(email_text)

        # Sender ke naam se sirf Email ID nikalna (e.g. "John Doe <john@gmail.com>" -> "john@gmail.com")
        match = re.search(r'<([^>]+)>', sender)
        to_email = match.group(1) if match else sender

        print(f"\n📧 From: {sender}")
        print(f"📝 Subject: {subject}")
        print(f"📊 Category: {category}")

        if category == "Spam":
            print("❌ Ignored (Spam)")
            continue

        reply = generate_reply(email_text)

        print("✍️ AI Reply Generated")

        if category == "Priority":
            print(f"🚀 Sending Email to {to_email}...")
            send_email(service, to_email, f"Re: {subject}", reply)
        else:
            print(f"💾 Saving as Draft for {to_email}...")
            save_draft(service, to_email, f"Re: {subject}", reply)

        print("-" * 50)

# ▶ MAIN
if __name__ == "__main__":
    service = authenticate()
    print("✅ Gmail Connected Successfully!")
    read_emails(service)
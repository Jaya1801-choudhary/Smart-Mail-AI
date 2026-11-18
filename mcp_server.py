# mcp_server.py
from mcp.server.fastmcp import FastMCP
import main # Tumhara existing main.py import kar rahe hain

# Server initialize karna
mcp = FastMCP("SmartMailAuthServer")

@mcp.tool()
def check_authentication_status() -> str:
    """Checks if the user is authenticated with Google (token.json exists)."""
    import os
    if os.path.exists('token.json'):
        return "User is Authenticated."
    return "User is NOT Authenticated. Needs to run authenticate()."

@mcp.tool()
def trigger_authentication() -> str:
    """Triggers the Google OAuth flow to login the user."""
    try:
        main.authenticate()
        return "Authentication successful."
    except Exception as e:
        return f"Authentication failed: {str(e)}"

@mcp.tool()
def trigger_logout() -> str:
    """Logs out the user by deleting the auth token."""
    success = main.logout()
    return "Logged out successfully." if success else "No active session found."

@mcp.tool()
def fetch_recent_emails(max_results: int = 5) -> str:
    """Fetches recent emails from the authenticated user's inbox."""
    try:
        service = main.authenticate() # Ensure we have the service
        # Hum read_emails ka logic thoda modify karke string me return karenge
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        email_summary = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_data.get('payload', {})
            
            # Simple extraction for tool output
            headers = payload.get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Unknown")
            
            email_summary.append(f"ID: {msg['id']} | From: {sender} | Sub: {subject}")
            
        return "\n".join(email_summary) if email_summary else "No new emails."
    except Exception as e:
         return f"Error fetching emails: {str(e)}"
@mcp.tool()
def download_attachments(message_id: str) -> str:
    """Downloads attachments from a specific email (using its message_id) and saves them locally."""
    import os
    import base64
    
    download_folder = "saved_attachments"
    
    try:
        service = main.authenticate()
        
        # Agar folder nahi hai, toh naya bana do
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
            
        # Email ka data fetch karo
        message = service.users().messages().get(userId='me', id=message_id).execute()
        parts = message.get('payload', {}).get('parts', [])
        
        downloaded_files = []
        
        # Email ke har hisse (part) ko check karo ki attachment hai ya nahi
        for part in parts:
            if part.get('filename'):
                filename = part['filename']
                attachment_id = part['body'].get('attachmentId')
                
                if attachment_id:
                    # Attachment ka actual data pull karo
                    attachment = service.users().messages().attachments().get(
                        userId='me', messageId=message_id, id=attachment_id
                    ).execute()
                    
                    # Data encode hota hai, usko decode karke save karo
                    file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
                    filepath = os.path.join(download_folder, filename)
                    
                    with open(filepath, 'wb') as f:
                        f.write(file_data)
                        
                    downloaded_files.append(filename)
                    
        if downloaded_files:
            return f"✅ Successfully downloaded: {', '.join(downloaded_files)} (Saved in '{download_folder}' folder)"
        else:
            return "❌ No attachments found in this email."
            
    except Exception as e:
        return f"Error downloading attachments: {str(e)}"
@mcp.tool()
def schedule_calendar_event(summary: str, start_time: str, end_time: str, description: str = "") -> str:
    """
    Schedules an event on Google Calendar. 
    AI should provide times in ISO format (e.g., '2026-07-10T10:00:00+05:30').
    """
    import os
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    try:
        if not os.path.exists('token.json'):
            return "❌ Error: Not authenticated. Please login from the UI first."
        
        # Load existing credentials directly
        creds = Credentials.from_authorized_user_file('token.json')
        
        # Calendar service build karna (Gmail ki jagah)
        calendar_service = build('calendar', 'v3', credentials=creds)
        
        event = {
          'summary': summary,
          'description': description,
          'start': {
            'dateTime': start_time,
            'timeZone': 'Asia/Kolkata', # Defaulting to IST
          },
          'end': {
            'dateTime': end_time,
            'timeZone': 'Asia/Kolkata',
          },
        }
        
        event_result = calendar_service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Event '{summary}' scheduled successfully! Link: {event_result.get('htmlLink')}"
        
    except Exception as e:
        return f"❌ Error scheduling calendar event: {str(e)}"
@mcp.tool()
def search_emails(query: str, max_results: int = 5) -> str:
    """Search for specific emails in Gmail using a keyword or query."""
    try:
        import main
        # Gmail authenticate karke service object lena
        service = main.authenticate()
        if not service:
            return "❌ Error: Gmail account not connected."
            
        # Gmail API ko search query bhejna
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
        
        if not messages:
            return f"No emails found matching your search: '{query}'"
            
        search_output = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = "No Subject"
            sender = "Unknown Sender"
            
            for header in headers:
                if header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'from':
                    sender = header['value']
                    
            search_output.append(f"📧 **From:** {sender}\n📌 **Subject:** {subject}\n---")
            
        return "\n".join(search_output)
        
    except Exception as e:
        return f"❌ Search failed: {str(e)}"
    
if __name__ == "__main__":
    # Ye server ko run karega
    print("Starting SmartMail MCP Server...")
    mcp.run()
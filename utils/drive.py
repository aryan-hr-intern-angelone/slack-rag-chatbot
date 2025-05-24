import io
import time
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from utils.embedding import get_pdf_text, get_text_chunks, get_vector_store, delete_index
from config.env import env

# Access Scopes
SCOPES = [
  "https://www.googleapis.com/auth/drive.readonly",
  "https://www.googleapis.com/auth/drive.metadata.readonly",
]

start_page_token = None

def load_start_token():
    global start_page_token
    try:
        if start_page_token is None:
            cred, _ = google.auth.default()
            service = build('drive', 'v3', credentials=cred)
            result = service.changes().getStartPageToken().execute()
            start_page_token = result['startPageToken']
        return start_page_token
    except Exception as e:
        print(f"Failed to load start token: {e}")
        return None

def save_start_token(token):
    global start_page_token
    try:
        start_page_token = token
    except Exception as e:
        print(f"Failed to save start token: {e}")

start_page_token = None

def load_start_token():
    global start_page_token
    try:
        if start_page_token is None:
            cred, _ = google.auth.default()
            service = build('drive', 'v3', credentials=cred)
            result = service.changes().getStartPageToken().execute()
            start_page_token = result['startPageToken']
        return start_page_token
    except Exception as e:
        print(f"Failed to load start token: {e}")
        return None

def save_start_token(token):
    global start_page_token
    try:
        start_page_token = token
    except Exception as e:
        print(f"Failed to save start token: {e}")

def handle_drive_notification():
    try:
      cred, _ = google.auth.default()
      saved_token = load_start_token()
      
      service = build('drive', 'v3', credentials=cred)

      start_page_token = load_start_token()

      response = service.changes().list(
          pageToken=start_page_token,
          spaces='drive',
          includeItemsFromAllDrives=True,
          supportsAllDrives=True
      ).execute()

      for change in response.get('changes', []):
          file_id = change['fileId']
          file_removed = change['removed']
          if file_removed:
            delete_index("llama-3", file_id)
          else:
            generate_file_index(file_id)

      new_token = response.get('newStartPageToken')
      if new_token:
          save_start_token(new_token)
    except HttpError as error:
      print(f"An error occurred: {error}")

def setup_change_watch():
    cred, _ = google.auth.default()
    try:
        service = build('drive', 'v3', credentials=cred)

        start_page_token = service.changes().getStartPageToken().execute()
        print(start_page_token)

        custom_expiration = int((time.time() + 86400) * 1000 *7)

        request_body = {
          "id": "hif39g",
          "type": "web_hook",
          "address": env.CUSTOM_WEBHOOK_URL,
          "expiration": custom_expiration
        }

        response = service.changes().watch(
          pageToken=start_page_token['startPageToken'],
          body=request_body,
        ).execute()

        print(response)

        changes = service.changes().list(
          pageToken=start_page_token['startPageToken'],
          spaces='drive'
        ).execute()

        print(changes)
    except HttpError as error:
       print(f"An error occurred: {error}")

def generate_file_index(file_id):
    cred, _ = google.auth.default()

    try:
        service = build('drive', 'v3', credentials=cred)

        file_metadata = service.files().get(
           fileId=file_id,
           fields='id, name, mimeType'  
        ).execute()

        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done=False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        file.seek(0)

        if file_metadata["mimeType"] == "application/pdf":
            text = get_pdf_text(file)
            chunks = get_text_chunks(text)
            get_vector_store(chunks, "llama-3", file_id)
            print("indexing completed")
        elif file_metadata["mimeType"] == "text/plain":
            text = file.getvalue().decode("utf-8")
            chunks = get_text_chunks(text)
            get_vector_store(chunks, "llama-3", file_id)
            print("indexing completed")

    except HttpError as error:
       print(f"An error occurred: {error}")
       file = None

    return file.getvalue()
    
def main():
  """Shows basic usage of the Drive v3 API.
  Prints the names and ids of the first 10 files the user has access to.
  """
  cred, _ = google.auth.default()

  try:
    # creates api client
    service = build("drive", "v3", credentials=cred)

    # Get all available folders
    folders = service.files().list(q="mimeType='application/vnd.google-apps.folder' and trashed=false", pageSize=10, fields="nextPageToken, files(id, name)").execute()
    folder = folders.get("files", [])
    
    print(f"Folder: {folder[0]['name']}")

    # Get first 10 files in the target folder
    results = (
        service.files()
        .list(q=f"'{folder[0]["id"]}' in parents", pageSize=10, fields="nextPageToken, files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if not items:
      print("No files found.")
      return
    print("Files:")
    print(f"Total Files: {len(items)}")
    for item in items:
      print(item)
      print(f"Downlading: {item["name"]}")
      try:
        generate_file_index(item["id"])
      except:
        continue
      
  except HttpError as error:
    print(f"An error occurred: {error}")

if __name__ == "__main__":
  # for testing
  main()
  setup_change_watch()
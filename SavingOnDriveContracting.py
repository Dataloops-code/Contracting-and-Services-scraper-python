import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from datetime import datetime, timedelta
from googleapiclient.discovery_cache.base import Cache

# Define a custom no-op cache to disable discovery caching
class NoOpCache(Cache):
    def get(self, url):
        return None

    def set(self, url, content):
        pass


class SavingOnDriveContracting:
    def __init__(self, credentials_dict):
        self.credentials_dict = credentials_dict
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service = None

    def authenticate(self):
        try:
            print("Authenticating Google Drive...")
            creds = Credentials.from_service_account_info(self.credentials_dict, scopes=self.scopes)

            # Pass the no-op cache to disable discovery caching
            self.service = build("drive", "v3", credentials=creds, cache=NoOpCache())
            print("Authentication successful.")
        except Exception as e:
            print(f"Authentication failed: {e}")
            raise

    def create_folder(self, folder_name, parent_folder_id=None):
        try:
            print(f"Attempting to create folder: {folder_name}")
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_folder_id:
                file_metadata["parents"] = [parent_folder_id]

            folder = self.service.files().create(body=file_metadata, fields="id").execute()
            print(f"Folder '{folder_name}' created with ID: {folder.get('id')}")
            return folder.get("id")
        except Exception as e:
            print(f"Failed to create folder '{folder_name}': {e}")
            raise

    def get_folder_id(self, folder_name):
        try:
            print(f"Looking for folder: {folder_name}")
            query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            response = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            folders = response.get('files', [])
            if folders:
                print(f"Found folder '{folder_name}' with ID: {folders[0]['id']}")
                return folders[0]['id']
            print(f"Folder '{folder_name}' not found.")
            return None
        except Exception as e:
            print(f"Error fetching folder ID for '{folder_name}': {e}")
            return None

    def upload_file(self, file_name, folder_id):
        try:
            print(f"Uploading file: {file_name}")
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            media = MediaFileUpload(file_name, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"File '{file_name}' uploaded with ID: {file.get('id')}")
            return file.get('id')
        except Exception as e:
            print(f"Failed to upload file '{file_name}': {e}")
            raise

    def save_files(self, files, folder_id=None):
        try:
            parent_folder_id = "1HDaiX9adrEsAx74dRlbmgMZMm_eeVyHM"
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            if folder_id is None:
                folder_id = self.get_folder_id(yesterday)
                if folder_id:
                    print(f"Folder '{yesterday}' already exists with ID: {folder_id}")
                else:
                    print(f"Folder '{yesterday}' does not exist. Creating it...")
                    try:
                        self.service.files().get(fileId=parent_folder_id).execute()
                    except Exception as e:
                        print(f"Parent folder validation failed: {e}")
                        raise
                    folder_id = self.create_folder(yesterday, parent_folder_id)

            for file_name in files:
                if os.path.exists(file_name):
                    self.upload_file(file_name, folder_id)
                else:
                    print(f"File not found: {file_name}")
        except Exception as e:
            print(f"Error in save_files: {e}")
            raise

    def list_files(self):
        try:
            print("Listing files on Google Drive...")
            results = self.service.files().list(pageSize=10, fields="files(id, name)").execute()
            for file in results.get("files", []):
                print(f"File: {file['name']} (ID: {file['id']})")
        except Exception as e:
            print(f"Error listing files: {e}")

import requests
from urllib.parse import quote
from utils import get_env

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

class SharePointGraphClient:
    def __init__(self):
        self.tenant_id = get_env("TENANT_ID")
        self.client_id = get_env("CLIENT_ID")
        self.client_secret = get_env("CLIENT_SECRET")

        self.site_host = get_env("SHAREPOINT_SITE_HOST")
        self.site_path = get_env("SHAREPOINT_SITE_PATH")

        self._token = None

    def get_access_token(self) -> str:
        if self._token:
            return self._token

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "client_credentials",
            "scope": "https://graph.microsoft.com/.default",
        }
        resp = requests.post(token_url, data=data, timeout=30)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.get_access_token()}"}

    def get_site_id(self) -> str:
        url = f"{GRAPH_BASE}/sites/{self.site_host}:{self.site_path}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()["id"]

    def get_default_drive_id(self, site_id: str) -> str:
        url = f"{GRAPH_BASE}/sites/{site_id}/drive"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()["id"]

    def file_exists(self, drive_id: str, sp_relative_path: str):
        safe_path = quote(sp_relative_path)
        url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{safe_path}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        if resp.status_code == 404:
            return False, None
        resp.raise_for_status()
        return True, resp.json()

    def upload_small_file(self, drive_id: str, sp_relative_path: str, content: bytes) -> dict:
        safe_path = quote(sp_relative_path)
        url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{safe_path}:/content"
        headers = {**self._headers(), "Content-Type": "application/octet-stream"}
        resp = requests.put(url, headers=headers, data=content, timeout=60)
        resp.raise_for_status()
        return resp.json()

    def upload_large_file_session(self, drive_id: str, sp_relative_path: str, content: bytes, chunk_size: int = 3276800) -> dict:
        safe_path = quote(sp_relative_path)
        create_url = f"{GRAPH_BASE}/drives/{drive_id}/root:/{safe_path}:/createUploadSession"
        resp = requests.post(create_url, headers=self._headers(), json={}, timeout=30)
        resp.raise_for_status()
        upload_url = resp.json()["uploadUrl"]

        total = len(content)
        start = 0
        while start < total:
            end = min(start + chunk_size, total) - 1
            chunk = content[start:end+1]
            headers = {
                "Content-Length": str(len(chunk)),
                "Content-Range": f"bytes {start}-{end}/{total}",
            }
            put = requests.put(upload_url, headers=headers, data=chunk, timeout=120)
            if put.status_code in (200, 201):
                return put.json()
            if put.status_code == 202:
                start = end + 1
                continue
            put.raise_for_status()

        raise RuntimeError("Upload did not complete")

    def upload_file_to_folder(self, folder_path: str, filename: str, content: bytes) -> dict:
        """
        Upload file into a specific SharePoint folder path in the default drive.
        folder_path example: "Shared Documents/Finance"
        """
        site_id = self.get_site_id()
        drive_id = self.get_default_drive_id(site_id)

        folder_path = folder_path.strip("/")

        sp_path = f"{folder_path}/{filename}"

        if len(content) <= 4 * 1024 * 1024:
            return self.upload_small_file(drive_id, sp_path, content)
        return self.upload_large_file_session(drive_id, sp_path, content)

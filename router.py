import os

# You can customize these rules anytime
ROUTES = [
    # keywords -> folder
    (["invoice", "bill", "payment", "receipt"], "Shared Documents/Finance"),
    (["resume", "cv", "offerletter"], "Shared Documents/HR"),
    (["assignment", "homework", "projectreport"], "Shared Documents/University"),
    (["legal", "court", "notice", "claim"], "Shared Documents/Legal"),
]

def route_sharepoint_folder(filename: str) -> str:
    """
    Decide where to upload the file in SharePoint based on filename keywords.
    """
    name = filename.lower()

    for keywords, folder in ROUTES:
        if any(k in name for k in keywords):
            return folder

    # fallback
    return os.getenv("SHAREPOINT_DEFAULT_FOLDER", "Shared Documents/Uploads")

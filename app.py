import streamlit as st
import os
from dotenv import load_dotenv
from sharepoint_graph import SharePointGraphClient
from router import route_sharepoint_folder
from utils import timestamped_name

load_dotenv()

st.set_page_config(page_title="Agent: Streamlit → SharePoint Router", layout="centered")
st.title("🤖 Agent File Router → SharePoint")
st.write("Upload a file. The app will **identify the correct SharePoint folder** and upload it with checkpointing.")

checkpoint_strategy = os.getenv("CHECKPOINT_STRATEGY", "VERSIONING").upper()
st.info(f"Checkpoint: **{checkpoint_strategy}** | Routing: **Rule-based**")

uploaded = st.file_uploader("Upload a file", type=None)

if uploaded:
    file_bytes = uploaded.getvalue()
    original_name = uploaded.name

    # Agent decision: choose folder
    chosen_folder = route_sharepoint_folder(original_name)

    st.write("### ✅ Routing Decision")
    st.write(f"**File:** {original_name}")
    st.write(f"**Redirect folder:** `{chosen_folder}`")

    client = SharePointGraphClient()

    # existence check needs drive_id, so reuse site/drive
    site_id = client.get_site_id()
    drive_id = client.get_default_drive_id(site_id)

    sp_path = f"{chosen_folder.strip('/')}/{original_name}"
    exists, _ = client.file_exists(drive_id, sp_path)

    final_name = original_name
    if exists:
        st.warning("File already exists in that folder.")
        if checkpoint_strategy == "RENAME":
            final_name = timestamped_name(original_name)
            st.write(f"Checkpoint applied → renamed to: **{final_name}**")
        else:
            st.write("Checkpoint applied → **SharePoint Versioning** (uploading new version).")

    if st.button("Upload to SharePoint"):
        try:
            result = client.upload_file_to_folder(chosen_folder, final_name, file_bytes)
            st.success("Uploaded successfully ✅")
            if "webUrl" in result:
                st.markdown(f"🔗 **Open in SharePoint:** {result['webUrl']}")
            st.json({
                "folder": chosen_folder,
                "final_filename": final_name,
                "checkpoint": checkpoint_strategy,
                "size_bytes": len(file_bytes)
            })
        except Exception as e:
            st.error(f"Upload failed: {e}")

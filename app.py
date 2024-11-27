import streamlit as st
from azure.storage.blob import BlobServiceClient
from update_index import main as update_index  # Replace with your actual indexing logic
import os

# Streamlit Web-App Configuration
st.set_page_config(page_title="Wiski-Datenverwaltung", layout="wide")

# Authentication Function
def authenticate(username, password):
    valid_username = st.secrets["APP_USERNAME"]
    valid_password = st.secrets["APP_PASSWORD"]
    return username == valid_username and password == valid_password

# Initialize Authentication State
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Initialize Feedback Messages
if "upload_messages" not in st.session_state:
    st.session_state["upload_messages"] = []
if "delete_messages" not in st.session_state:
    st.session_state["delete_messages"] = []

# Show Login Screen if Not Authenticated
if not st.session_state["authenticated"]:
    with st.container():
        st.title("🔒 Wiski-Datenverwaltung Login")
        st.write("Bitte melde dich an, um fortzufahren.")
        username = st.text_input("Benutzername")
        password = st.text_input("Passwort", type="password")
        if st.button("Anmelden"):
            if authenticate(username, password):
                st.session_state["authenticated"] = True
                st.rerun()  # Refresh the app to show the main content
            else:
                st.error("❌ Ungültiger Benutzername oder Passwort.")
    st.stop()  # Stop further execution if not authenticated

# Azure Blob Storage Configuration
connection_string = st.secrets["AZURE_BLOB_CONNECTION_STRING"]
container_name = st.secrets["AZURE_BLOB_CONTAINER_NAME"]
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

def list_files_with_metadata():
    """List all files in Blob Storage with their last modified date."""
    blobs = container_client.list_blobs()
    files = [{"name": blob.name, "last_modified": blob.last_modified} for blob in blobs]
    files.sort(key=lambda x: x["last_modified"], reverse=True)
    return files

# Main Application
st.title("🤖 Wiski-Datenverwaltung")
st.markdown(
    """
    Willkommen! Hier kannst du die Dateien für Wiski ganz einfach verwalten. 
    Ob neue Dateien hochladen oder alte löschen – diese App macht's dir so einfach wie möglich!
    """
)

# Display Success Messages After Rerun
if st.session_state["upload_messages"]:
    for message in st.session_state["upload_messages"]:
        if message["type"] == "success":
            st.success(message["text"])
        elif message["type"] == "error":
            st.error(message["text"])
    st.session_state["upload_messages"] = []  # Clear messages after displaying

if st.session_state["delete_messages"]:
    for message in st.session_state["delete_messages"]:
        if message["type"] == "success":
            st.success(message["text"])
        elif message["type"] == "error":
            st.error(message["text"])
    st.session_state["delete_messages"] = []  # Clear messages after displaying

# Tabs for Better Organization
tab1, tab2 = st.tabs(["📂 Aktuelle Dateien", "📤 Dateien hochladen"])

# Tab 1: Display Current Files
with tab1:
    st.subheader("📂 Aktuelle Dateien")
    files_with_metadata = list_files_with_metadata()
    total_files = len(files_with_metadata)

    st.write(f"Hier siehst du alle Dateien, auf die Wiski aktuell Zugriff hat. Aktuell sind es **{total_files}** Dateien.")

    if files_with_metadata:
        selected_files = []
        delete_button = st.button("❌ Lösche ausgewählte Dateien")

        for file in files_with_metadata:
            col1, col2 = st.columns([6, 3])
            selected = col1.checkbox(f"📄 {file['name']}", key=file["name"])
            if selected:
                selected_files.append(file["name"])
            col2.write(f"🕒 {file['last_modified'].strftime('%d.%m.%Y %H:%M')}")

        if delete_button:
            if selected_files:
                for file_name in selected_files:
                    try:
                        container_client.delete_blob(file_name)
                        st.session_state["delete_messages"].append({
                            "type": "success",
                            "text": f"❌ {file_name} wurde erfolgreich gelöscht! Wiski wird jetzt aktualisiert..."
                        })
                    except Exception as e:
                        st.session_state["delete_messages"].append({
                            "type": "error",
                            "text": f"❌ Fehler beim Löschen von {file_name}: {e}"
                        })
                if any(msg["type"] == "success" for msg in st.session_state["delete_messages"]):
                    try:
                        update_index()
                        st.session_state["delete_messages"].append({
                            "type": "success",
                            "text": "🤖 Wiski wurde erfolgreich aktualisiert!"
                        })
                    except Exception as e:
                        st.session_state["delete_messages"].append({
                            "type": "error",
                            "text": f"❌ Fehler beim Aktualisieren des Index: {e}"
                        })
                st.rerun()  # Trigger a rerun after all deletions
            else:
                st.warning("⚠️ Du hast keine Dateien ausgewählt.")

    else:
        st.write("🚫 Es sind keine Dateien im Datenordner vorhanden.")

# Tab 2: Upload Files
with tab2:
    st.subheader("📤 Dateien hochladen")
    st.info("💡 Unterstützte Dateitypen: PDF, TXT, DOCX, PPTX, XLSX, PNG, JSON, HTML, XML.")

    uploaded_files = st.file_uploader(
        "Wähle Dateien aus", type=["pdf", "txt", "docx", "pptx", "xlsx", "png", "json", "html", "xml"], accept_multiple_files=True
    )
    if st.button("📤 Dateien hochladen") and uploaded_files:
        upload_errors = []
        upload_successes = []
        for uploaded_file in uploaded_files:
            try:
                container_client.upload_blob(uploaded_file.name, uploaded_file, overwrite=True)
                upload_successes.append(f"✅ {uploaded_file.name} wurde erfolgreich hochgeladen!")
            except Exception as e:
                upload_errors.append(f"❌ Fehler beim Hochladen von {uploaded_file.name}: {e}")

        # Update the index if at least one upload was successful
        if upload_successes:
            try:
                update_index()
                upload_successes.append("🤖 Wiski wurde erfolgreich aktualisiert!")
            except Exception as e:
                upload_errors.append(f"❌ Fehler beim Aktualisieren des Index: {e}")

        # Store messages in session_state
        for msg in upload_successes:
            st.session_state["upload_messages"].append({
                "type": "success",
                "text": msg
            })
        for msg in upload_errors:
            st.session_state["upload_messages"].append({
                "type": "error",
                "text": msg
            })

        st.rerun()  # Trigger a single rerun after all uploads

    st.markdown("---")
    st.write("Nachdem die Dateien hochgeladen wurden, findest du sie im Tab **📂 Aktuelle Dateien**.")

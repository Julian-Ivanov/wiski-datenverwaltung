import streamlit as st
from azure.storage.blob import BlobServiceClient
from update_index import main as update_index  # Replace with your actual indexing logic
import os

# Streamlit Web-App
st.set_page_config(page_title="Wiski-Datenverwaltung", layout="wide")

# Authentication
def authenticate(username, password):
    # Replace with your desired username and password
    valid_username = st.secrets["APP_USERNAME"]
    valid_password = st.secrets["APP_PASSWORD"]
    return username == valid_username and password == valid_password

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Wiski-Datenverwaltung Login")
    st.write("Bitte melde dich an, um fortzufahren.")
    username = st.text_input("Benutzername")
    password = st.text_input("Passwort", type="password")
    if st.button("Anmelden"):
        if authenticate(username, password):
            st.success("✅ Anmeldung erfolgreich!")
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("❌ Ungültiger Benutzername oder Passwort.")
    st.stop()

# Azure Blob Storage Configuration
connection_string = st.secrets["AZURE_BLOB_CONNECTION_STRING"]
container_name = st.secrets["AZURE_BLOB_CONTAINER_NAME"]
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)


def list_files_with_metadata():
    """List all files in Blob Storage with their last modified date."""
    blobs = container_client.list_blobs()
    files = [{"name": blob.name, "last_modified": blob.last_modified} for blob in blobs]
    # Sort files by last modified date in descending order
    files.sort(key=lambda x: x["last_modified"], reverse=True)
    return files


def upload_file(file, file_name):
    """Upload a file to Blob Storage and update the index."""
    container_client.upload_blob(file_name, file, overwrite=True)
    st.success(f"✅ {file_name} wurde erfolgreich hochgeladen! Der Index wird jetzt aktualisiert...")
    update_index()
    st.success("🤖 Wiski wurde erfolgreich aktualisiert!")


def delete_file(file_name):
    """Delete a file from Blob Storage and update the index."""
    container_client.delete_blob(file_name)
    st.success(f"❌ {file_name} wurde erfolgreich gelöscht! Wiski wird jetzt aktualisiert...")
    update_index()
    st.success("🤖 Wiski wurde erfolgreich aktualisiert!")


# Main Application
st.title("🤖 Wiski-Datenverwaltung")
st.markdown(
    """
    Willkommen! Hier kannst du die Dateien für Wiski ganz einfach verwalten. 
    Ob neue Dateien hochladen oder alte löschen – diese App macht's dir so einfach wie möglich!
    """
)

# Tabs for better organization
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

        if delete_button and selected_files:
            for file_name in selected_files:
                delete_file(file_name)
            st.success("✅ Die ausgewählten Dateien wurden erfolgreich gelöscht!")
        elif delete_button and not selected_files:
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
    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_file(uploaded_file, uploaded_file.name)

    st.markdown("---")
    st.write("Nachdem die Dateien hochgeladen wurden, findest du sie im Tab **Aktuelle Dateien**.")

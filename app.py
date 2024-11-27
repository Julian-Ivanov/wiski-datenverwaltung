import streamlit as st
from azure.storage.blob import BlobServiceClient
from update_index import main as update_index  # Ersetze dies mit deinem tatsächlichen Indexierungs-Logik
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure Blob Storage Configuration
connection_string = os.getenv("AZURE_BLOB_CONNECTION_STRING")
container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME")
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)


def list_files_with_metadata():
    """Listet alle Dateien im Blob-Speicher mit ihrem Änderungsdatum auf."""
    blobs = container_client.list_blobs()
    files = [{"name": blob.name, "last_modified": blob.last_modified} for blob in blobs]
    # Dateien nach Änderungsdatum absteigend sortieren
    files.sort(key=lambda x: x["last_modified"], reverse=True)
    return files


def upload_file(file, file_name):
    """Lädt eine Datei in den Blob-Speicher hoch und aktualisiert den Index."""
    container_client.upload_blob(file_name, file, overwrite=True)
    st.success(f"✅ {file_name} wurde erfolgreich hochgeladen! Der Index wird jetzt aktualisiert...")
    update_index()
    st.success("🤖 Wiski wurde erfolgreich aktualisiert!")


def delete_file(file_name):
    """Löscht eine Datei aus dem Blob-Speicher und aktualisiert den Index."""
    container_client.delete_blob(file_name)
    st.success(f"❌ {file_name} wurde erfolgreich gelöscht! Wiski wird jetzt aktualisiert...")
    update_index()
    st.success("🤖 Wiski wurde erfolgreich aktualisiert!")


# Streamlit Web-App
st.set_page_config(page_title="Wiski-Datenverwaltung", layout="wide")

st.title("🤖 Wiski-Datenverwaltung")
st.markdown(
    """
    Willkommen! Hier kannst du die Dateien für Wiski ganz einfach verwalten. 
    Ob neue Dateien hochladen oder alte löschen – diese App macht's dir so einfach wie möglich!
    """
)

# Tabs für bessere Organisation
tab1, tab2 = st.tabs(["📂 Aktuelle Dateien", "📤 Dateien hochladen"])

# Tab 1: Aktuelle Dateien anzeigen
with tab1:
    st.subheader("📂 Aktuelle Dateien")
    # Fetch files with metadata
    files_with_metadata = list_files_with_metadata()
    total_files = len(files_with_metadata)  # Total number of files

    st.write(f"Hier siehst du alle Dateien, auf die Wiski aktuell Zugriff hat. Aktuell sind es **{total_files}** Dateien. Wenn du Dateien löschen möchtest, wähle die entsprechenden Dateien aus und klicke auf den Button.")

    if files_with_metadata:
        # Container to store selected files
        selected_files = []

        # Add the delete button above the file list
        delete_button = st.button("❌ Lösche ausgewählte Dateien")

        # Create a checkbox for each file
        for file in files_with_metadata:
            col1, col2 = st.columns([6, 3])
            # File name and checkbox
            selected = col1.checkbox(f"📄 {file['name']}", key=file["name"])
            if selected:
                selected_files.append(file["name"])
            # File last modified date
            col2.write(f"🕒 {file['last_modified'].strftime('%d.%m.%Y %H:%M')}")

        # Handle file deletion when button is clicked
        if delete_button and selected_files:
            for file_name in selected_files:
                delete_file(file_name)
            st.success("✅ Die ausgewählten Dateien wurden erfolgreich gelöscht!")
        elif delete_button and not selected_files:
            st.warning("⚠️ Du hast keine Dateien ausgewählt.")
    else:
        st.write("🚫 Es sind keine Dateien im Datenordner vorhanden.")

# Tab 2: Dateien hochladen
with tab2:
    st.subheader("📤 Dateien hochladen")
    st.write(
        "Lade hier neue Dateien für Wiski hoch. Sobald die Dateien hochgeladen sind, "
        "werden sie automatisch Wiski zur Verfügung gestellt."
    )
    st.info("💡 Unterstützte Dateitypen: PDF, TXT, DOCX, PPTX, XLSX, PNG, JSON, HTML, XML.")

    uploaded_files = st.file_uploader(
        "Wähle Dateien aus", type=["pdf", "txt", "docx", "pptx", "xlsx", "png", "json", "html", "xml"], accept_multiple_files=True
    )
    if uploaded_files:
        for uploaded_file in uploaded_files:
            upload_file(uploaded_file, uploaded_file.name)

    st.markdown("---")
    st.write("Nachdem die Dateien hochgeladen wurden, findest du sie im Tab **Aktuelle Dateien**.")

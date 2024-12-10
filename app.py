import streamlit as st
from azure.storage.blob import BlobServiceClient
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
if "selected_to_delete" not in st.session_state:
    st.session_state.selected_to_delete = []
if "selected_files" not in st.session_state:
    st.session_state.selected_files = []
if "upload_success" not in st.session_state:
    st.session_state.upload_success = False

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
                st.rerun()
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
    return files

def upload_file_to_blob(file, file_name):
    container_client.upload_blob(file_name, file, overwrite=True)

def delete_file_from_blob(file_name):
    container_client.delete_blob(file_name)
    st.success(f"❌ {file_name} wurde erfolgreich gelöscht!")

st.title("🤖 Wiski-Datenverwaltung")
st.markdown(
    """
    Willkommen! Hier kannst du die Dateien für Wiski ganz einfach verwalten. 
    Ob neue Dateien hochladen oder alte löschen – diese App macht's dir so einfach wie möglich!
    """
)

tab1, tab2 = st.tabs(["📂 Aktuelle Dateien", "📤 Dateien hochladen"])

with tab1:
    st.subheader("📂 Aktuelle Dateien")

    # If we have files awaiting deletion confirmation, show it at the top
    if st.session_state.selected_to_delete:
        st.warning("Bist du sicher, die ausgewählten Dateien zu löschen?")
        st.write("**Ausgewählte Dateien:**")
        for f in st.session_state.selected_to_delete:
            st.write(f"📄 {f}")
            
        col_confirm, col_cancel = st.columns([1,1])
        with col_confirm:
            if st.button("Ja, löschen"):
                for file_name in st.session_state.selected_to_delete:
                    delete_file_from_blob(file_name)
                st.session_state.selected_to_delete = []
                st.rerun()

        with col_cancel:
            if st.button("Abbrechen"):
                st.session_state.selected_to_delete = []
                st.info("Löschvorgang abgebrochen.")
                st.rerun()

        # Stop here so the rest of the UI doesn't appear below the prompt
        st.stop()

    # Normal UI if no confirmation is needed
    files_with_metadata = list_files_with_metadata()

    top_col1, top_col2, top_col3 = st.columns([1,2,3])
    with top_col1:
        if st.button("🔄 Aktualisieren"):
            st.rerun()

    with top_col3:
        sort_option = st.selectbox(
            "Sortierungsoptionen",
            ["Name (alphabetisch)", "Zuletzt geändert (neueste zuerst)", "Zuletzt geändert (älteste zuerst)"],
            label_visibility="collapsed"
        )

    if sort_option == "Name (alphabetisch)":
        files_with_metadata.sort(key=lambda x: x["name"].lower())
    elif sort_option == "Zuletzt geändert (neueste zuerst)":
        files_with_metadata.sort(key=lambda x: x["last_modified"], reverse=True)
    else:
        files_with_metadata.sort(key=lambda x: x["last_modified"])

    total_files = len(files_with_metadata)
    st.write(f"Hier siehst du alle Dateien, auf die Wiski aktuell Zugriff hat. Aktuell sind es **{total_files}** Dateien.")

    if files_with_metadata:
        with st.form("file_selection_form"):
            delete_button = st.form_submit_button("❌ Lösche ausgewählte Dateien")

            file_container = st.container()

            header_col1, header_col2, header_col3 = file_container.columns([1,6,3])
            header_col1.markdown("**Auswahl**")
            header_col2.markdown("**Dateiname**")
            header_col3.markdown("**Zuletzt geändert**")

            selected_files = []
            for file in files_with_metadata:
                col_check, col_name, col_date = file_container.columns([1,6,3])
                selected = col_check.checkbox("Datei auswählen", key=file["name"], label_visibility="collapsed")
                col_name.write(f"📄 {file['name']}")
                col_date.write(f"🕒 {file['last_modified'].strftime('%d.%m.%Y %H:%M')}")

                if selected:
                    selected_files.append(file["name"])

            if delete_button:
                if selected_files:
                    st.session_state.selected_to_delete = selected_files
                    st.rerun()
                else:
                    st.warning("⚠️ Du hast keine Dateien ausgewählt.")
    else:
        st.write("🚫 Es sind keine Dateien im Datenordner vorhanden.")

with tab2:
    st.subheader("📤 Dateien hochladen")
    top_message_placeholder = st.empty()
    st.info("💡 Unterstützte Dateitypen: PDF, TXT, DOCX, PPTX, XLSX, PNG, JSON, HTML, XML.")

    selected_files = st.file_uploader(
        "Wähle Dateien aus", 
        type=["pdf", "txt", "docx", "pptx", "xlsx", "png", "json", "html", "xml"], 
        accept_multiple_files=True
    )

    if selected_files:
        st.session_state.selected_files = selected_files

    if st.session_state.selected_files:
        st.write("### Ausgewählte Dateien:")
        for uploaded_file in st.session_state.selected_files:
            st.write(f"📄 {uploaded_file.name}")

        if st.button("📤 Hochladen"):
            with st.spinner("Dateien werden hochgeladen..."):
                for uploaded_file in st.session_state.selected_files:
                    upload_file_to_blob(uploaded_file, uploaded_file.name)
            st.session_state.selected_files = []
            top_message_placeholder.success("Die Dateien wurden erfolgreich hochgeladen! Wiski wird in ca. 5 Minuten aktualisiert.")

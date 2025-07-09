import streamlit as st
import json
import os
from PIL import Image
import qrcode
from datetime import datetime

# ------------------------ Config ------------------------
BASE_PATH = "."
DATA_FILES = {
    "users": "users.json",
    "children": "children.json",
    "activities": "activities.json",
    "milestones": "milestones.json",
    "health": "health.json",
    "todos": "todos.json",
    "reminders": "reminders.json",
    "messages": "messages.json",
    "expenses": "expenses.json",
    "wellness": "wellness.json"
}
FOLDER_PATHS = {
    "photos": "photos",
    "qrcodes": "qrcodes",
    "documents": "documents"
}
for path in FOLDER_PATHS.values():
    os.makedirs(path, exist_ok=True)

LOGO_FILE = os.path.join(FOLDER_PATHS["photos"], "cats_cradle_logo.png")

# ------------------------ Utils ------------------------
@st.cache_data
def load_json(file):
    path = os.path.join(BASE_PATH, file)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)
    with open(path, "r") as f:
        return json.load(f)

def save_json(file, data):
    path = os.path.join(BASE_PATH, file)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def password_valid(password):
    if len(password) < 6:
        return False
    has_number = any(char.isdigit() for char in password)
    has_special = any(not char.isalnum() for char in password)
    return has_number and has_special

def generate_qr_code(child_id, info):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(FOLDER_PATHS["qrcodes"], f"{child_id}.png")
    img.save(path)
    return path

def show_logo():
    if os.path.exists(LOGO_FILE):
        st.image(LOGO_FILE, width=200)

# ------------------------ Session ------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "sos_log" not in st.session_state:
    st.session_state.sos_log = []

# ------------------------ Auth Pages ------------------------
def register_page():
    st.title("Register")
    show_logo()
    full_name = st.text_input("Full Name")
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if not password_valid(password):
            st.error("Password must be at least 6 characters and include numbers and special characters.")
            return
        users = load_json(DATA_FILES["users"])
        if email in users:
            st.error("Email already registered.")
            return
        users[email] = {"full_name": full_name, "password": password}
        save_json(DATA_FILES["users"], users)
        st.success("Registration successful! You can now log in.")

def login_page():
    st.title("Login")
    show_logo()
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_json(DATA_FILES["users"])
        if email in users and users[email]["password"] == password:
            st.session_state.user = {"email": email, "full_name": users[email]["full_name"]}
            st.success("Login successful!")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

# ------------------------ Child Management ------------------------
def add_child_page():
    st.header("Add a Child")
    name = st.text_input("Child Name")
    age = st.number_input("Age", min_value=0, max_value=25, step=1)
    notes = st.text_area("Notes")
    photo = st.file_uploader("Upload Photo", type=["png", "jpg", "jpeg"])
    if st.button("Save Child"):
        if not name:
            st.error("Child name is required.")
            return
        children = load_json(DATA_FILES["children"])
        child_id = str(len(children) + 1)
        photo_path = ""
        if photo:
            photo_path = os.path.join(FOLDER_PATHS["photos"], f"{child_id}_{photo.name}")
            with open(photo_path, "wb") as f:
                f.write(photo.read())
        children[child_id] = {
            "name": name,
            "age": age,
            "notes": notes,
            "photo": photo_path,
            "parent_email": st.session_state.user["email"]
        }
        save_json(DATA_FILES["children"], children)
        info = f"I’m lost! My name is {name}. Contact my parent: {st.session_state.user['email']}"
        generate_qr_code(child_id, info)
        st.success("Child added successfully!")

def view_children_page():
    st.header("Your Children")
    children = load_json(DATA_FILES["children"])
    user_email = st.session_state.user["email"]
    user_children = {cid: c for cid, c in children.items() if c["parent_email"] == user_email}
    if not user_children:
        st.info("You have no children added yet.")
        return
    for cid, child in user_children.items():
        with st.expander(f"{child['name']} (Age {child['age']})"):
            if child["photo"]:
                st.image(child["photo"], width=150)
            st.text(f"Notes: {child['notes']}")
            if st.button(f"Show QR Code for {child['name']}", key=f"qr_{cid}"):
                qr_path = os.path.join(FOLDER_PATHS["qrcodes"], f"{cid}.png")
                if os.path.exists(qr_path):
                    st.image(qr_path)
                else:
                    st.error("QR code not found.")
            if st.button(f"SOS Alert for {child['name']}", key=f"sos_{cid}"):
                st.session_state.sos_log.append(f"SOS sent for {child['name']}")
                st.warning(f"SOS alert sent for {child['name']}!")

def sos_log_page():
    st.header("SOS Log")
    if not st.session_state.sos_log:
        st.info("No SOS alerts yet.")
    else:
        for log in st.session_state.sos_log:
            st.write(log)

# ------------------------ Main App ------------------------
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.user['full_name']}")
    choice = st.sidebar.selectbox("Menu", [
        "Dashboard", "Add Child", "SOS Log", "Logout"
    ])
    if choice == "Dashboard":
        view_children_page()
    elif choice == "Add Child":
        add_child_page()
    elif choice == "SOS Log":
        sos_log_page()
    elif choice == "Logout":
        st.session_state.user = None
        st.experimental_rerun()

# ------------------------ Main ------------------------
def main():
    st.set_page_config(page_title="Cat’s Cradle", layout="centered")
    if not st.session_state.user:
        auth_choice = st.sidebar.radio("Auth", ["Login", "Register"])
        if auth_choice == "Login":
            login_page()
        else:
            register_page()
    else:
        main_app()

if __name__ == "__main__":
    main()

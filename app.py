import streamlit as st
import json
import os
import qrcode
from datetime import datetime

# ------------------------ CONFIG ------------------------
BASE_PATH = "."
LOGO_PATH = "photos/cats_cradle_logo.png"

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
for file in DATA_FILES.values():
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)

# ------------------------ UTILS ------------------------
def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)

def load_json(file):
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def password_valid(password):
    return len(password) >= 6 and any(c.isdigit() for c in password) and any(not c.isalnum() for c in password)

def generate_qr_code(child_id, info):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(FOLDER_PATHS["qrcodes"], f"{child_id}.png")
    img.save(path)
    return path

# ------------------------ SESSION INIT ------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "sos_log" not in st.session_state:
    st.session_state.sos_log = []

# ------------------------ AUTH ------------------------
def register_page():
    st.title("Register")
    show_logo()
    full_name = st.text_input("Full Name")
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if not password_valid(password):
            st.error("Password must be at least 6 characters with numbers and special characters.")
            return
        users = load_json(DATA_FILES["users"])
        if email in users:
            st.error("Email already registered.")
            return
        users[email] = {"full_name": full_name, "password": password}
        save_json(DATA_FILES["users"], users)
        st.success("✅ Registered! Now log in.")

def login_page():
    st.title("Login")
    show_logo()
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_json(DATA_FILES["users"])
        if email in users and users[email]["password"] == password:
            st.session_state.user = {"email": email, "full_name": users[email]["full_name"]}
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")

# ------------------------ CHILD ------------------------
def add_child_page():
    st.header("Add a Child")
    show_logo()
    name = st.text_input("Child Name")
    age = st.number_input("Age", 0, 25, step=1)
    notes = st.text_area("Notes")
    parent2_name = st.text_input("Other Parent/Guardian Name (Optional)")
    parent2_email = st.text_input("Other Parent/Guardian Email (Optional)")
    parent2_number = st.text_input("Other Parent/Guardian Number (Optional)")
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
            "parent_email": st.session_state.user["email"],
            "parent2_name": parent2_name,
            "parent2_email": parent2_email,
            "parent2_number": parent2_number
        }
        save_json(DATA_FILES["children"], children)
        info = f"I’m lost! My name is {name}. Contact my parent: {st.session_state.user['email']}"
        generate_qr_code(child_id, info)
        st.success("✅ Child added!")

def view_children_page():
    st.header("Your Children")
    show_logo()
    children = load_json(DATA_FILES["children"])
    user_email = st.session_state.user["email"]
    user_children = {cid: c for cid, c in children.items() if c["parent_email"] == user_email}
    if not user_children:
        st.info("No children yet.")
        return
    for cid, child in user_children.items():
        with st.expander(f"{child['name']} (Age {child['age']})"):
            if child["photo"]:
                st.image(child["photo"], width=150)
            st.text(f"Notes: {child['notes']}")
            st.text(f"Primary Parent Email: {child['parent_email']}")
            if child.get("parent2_name"):
                st.text(f"Other Parent: {child['parent2_name']}")
                st.text(f"Email: {child['parent2_email']}")
                st.text(f"Number: {child['parent2_number']}")
            if st.button(f"Show QR for {child['name']}", key=f"qr_{cid}"):
                qr_path = os.path.join(FOLDER_PATHS["qrcodes"], f"{cid}.png")
                if os.path.exists(qr_path):
                    st.image(qr_path)
            if st.button(f"SOS Alert for {child['name']}", key=f"sos_{cid}"):
                st.session_state.sos_log.append(f"SOS sent for {child['name']}")
                st.warning(f"SOS alert sent for {child['name']}!")

def sos_log_page():
    st.header("SOS Log")
    show_logo()
    if not st.session_state.sos_log:
        st.info("No SOS alerts yet.")
    else:
        for log in st.session_state.sos_log:
            st.write(log)

# ------------------------ OTHER FEATURES ------------------------
def generic_list_page(title, data_file, fields):
    st.header(title)
    show_logo()
    data = load_json(DATA_FILES[data_file])
    user_email = st.session_state.user["email"]

    with st.form("entry_form"):
        entries = {field: st.text_input(field) for field in fields}
        submitted = st.form_submit_button("Save")
        if submitted:
            key = str(len(data) + 1)
            data[key] = {
                "parent": user_email,
                "timestamp": datetime.now().isoformat(),
                **entries
            }
            save_json(DATA_FILES[data_file], data)
            st.success("Saved!")

    st.subheader("Your Entries")
    for item in data.values():
        if item["parent"] == user_email:
            st.markdown(f"- {item['timestamp']}")
            for field in fields:
                st.text(f"{field}: {item.get(field, '')}")

def todos_page():
    st.header("To-Do Lists")
    show_logo()
    todos = load_json(DATA_FILES["todos"])
    user_email = st.session_state.user["email"]
    task = st.text_input("Task")
    if st.button("Add Task"):
        key = str(len(todos) + 1)
        todos[key] = {"parent": user_email, "task": task, "done": False}
        save_json(DATA_FILES["todos"], todos)
        st.success("Added!")
    st.subheader("Your Tasks")
    for k, t in todos.items():
        if t["parent"] == user_email:
            if st.checkbox(t["task"], value=t["done"], key=k):
                t["done"] = True
                save_json(DATA_FILES["todos"], todos)

def documents_page():
    st.header("Documents")
    show_logo()
    documents = FOLDER_PATHS["documents"]
    uploaded = st.file_uploader("Upload", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded:
        path = os.path.join(documents, uploaded.name)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        st.success(f"Uploaded {uploaded.name}")
    st.subheader("Your Documents")
    for fname in os.listdir(documents):
        st.markdown(f"- {fname}")

# ------------------------ MAIN APP ------------------------
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.user['full_name']}")
    choice = st.sidebar.selectbox("Menu", [
        "Dashboard", "Add Child", "SOS Log",
        "Activity Tracking", "Milestone Tracking", "Health Tracking",
        "To-Do Lists", "Reminders", "Document Upload",
        "Expenses", "Secure Messaging", "Mental Wellness", "Logout"
    ])
    if choice == "Dashboard": view_children_page()
    elif choice == "Add Child": add_child_page()
    elif choice == "SOS Log": sos_log_page()
    elif choice == "Activity Tracking": generic_list_page("Activity Tracking", "activities", ["Child's Name", "Activity Type", "Notes"])
    elif choice == "Milestone Tracking": generic_list_page("Milestone Tracking", "milestones", ["Child's Name", "Milestone", "Notes"])
    elif choice == "Health Tracking": generic_list_page("Health Tracking", "health", ["Child's Name", "Event", "Details"])
    elif choice == "To-Do Lists": todos_page()
    elif choice == "Reminders": generic_list_page("Reminders", "reminders", ["Reminder Text"])
    elif choice == "Document Upload": documents_page()
    elif choice == "Expenses": generic_list_page("Expenses", "expenses", ["Description", "Amount"])
    elif choice == "Secure Messaging": generic_list_page("Secure Messaging", "messages", ["Message"])
    elif choice == "Mental Wellness": generic_list_page("Mental Wellness", "wellness", ["Mood (0-10)", "Notes"])
    elif choice == "Logout":
        st.session_state.user = None
        st.experimental_rerun()

# ------------------------ MAIN ------------------------
def main():
    st.set_page_config(page_title="Cat's Cradle", layout="centered")
    if not st.session_state.user:
        page = st.sidebar.radio("Auth", ["Login", "Register"])
        if page == "Login": login_page()
        else: register_page()
    else:
        main_app()

if __name__ == "__main__":
    main()

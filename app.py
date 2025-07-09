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

# ------------------------ Utils ------------------------
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

# ------------------------ Session ------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "sos_log" not in st.session_state:
    st.session_state.sos_log = []

# ------------------------ Auth Pages ------------------------
def register_page():
    st.title("🐱 Cat’s Cradle - Register")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
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
        st.success("Registration successful. You can now log in.")

def login_page():
    st.title("🐱 Cat’s Cradle - Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_json(DATA_FILES["users"])
        if email in users and users[email]["password"] == password:
            st.session_state.user = {"email": email, "full_name": users[email]["full_name"]}
            st.success("Login successful!")
            st.rerun()
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

# ------------------------ New Features ------------------------
def activity_tracking_page():
    st.header("Baby Activity Tracking")
    activities = load_json(DATA_FILES["activities"])
    user_email = st.session_state.user["email"]
    child_name = st.text_input("Child's Name")
    activity = st.selectbox("Activity Type", ["Feeding", "Sleep", "Diaper Change", "Medication", "Growth"])
    notes = st.text_area("Details / Notes")
    if st.button("Save Activity"):
        key = str(len(activities) + 1)
        activities[key] = {
            "parent": user_email,
            "child": child_name,
            "activity": activity,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["activities"], activities)
        st.success("Activity saved!")

    st.subheader("Your Logged Activities")
    for a in activities.values():
        if a["parent"] == user_email:
            st.markdown(f"**{a['child']}** - {a['activity']} at {a['timestamp']}")
            st.text(a["notes"])

def milestone_tracking_page():
    st.header("Milestone Tracking")
    milestones = load_json(DATA_FILES["milestones"])
    user_email = st.session_state.user["email"]
    child_name = st.text_input("Child's Name")
    milestone = st.text_input("Milestone Achieved")
    notes = st.text_area("Notes")
    if st.button("Save Milestone"):
        key = str(len(milestones) + 1)
        milestones[key] = {
            "parent": user_email,
            "child": child_name,
            "milestone": milestone,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["milestones"], milestones)
        st.success("Milestone saved!")

    st.subheader("Your Milestones")
    for m in milestones.values():
        if m["parent"] == user_email:
            st.markdown(f"**{m['child']}** - {m['milestone']} at {m['timestamp']}")
            st.text(m["notes"])

def health_tracking_page():
    st.header("Health Tracking")
    health = load_json(DATA_FILES["health"])
    user_email = st.session_state.user["email"]
    child_name = st.text_input("Child's Name")
    health_event = st.text_input("Event (e.g. Vaccination, Doctor Visit, Symptom)")
    notes = st.text_area("Details")
    if st.button("Save Health Event"):
        key = str(len(health) + 1)
        health[key] = {
            "parent": user_email,
            "child": child_name,
            "event": health_event,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["health"], health)
        st.success("Health record saved!")

    st.subheader("Your Health Records")
    for h in health.values():
        if h["parent"] == user_email:
            st.markdown(f"**{h['child']}** - {h['event']} at {h['timestamp']}")
            st.text(h["notes"])

def todos_page():
    st.header("To-Do Lists")
    todos = load_json(DATA_FILES["todos"])
    user_email = st.session_state.user["email"]
    task = st.text_input("Task")
    if st.button("Add Task"):
        key = str(len(todos) + 1)
        todos[key] = {
            "parent": user_email,
            "task": task,
            "done": False
        }
        save_json(DATA_FILES["todos"], todos)
        st.success("Task added!")

    st.subheader("Your Tasks")
    for k, t in todos.items():
        if t["parent"] == user_email:
            if st.checkbox(t["task"], value=t["done"], key=k):
                t["done"] = True
    save_json(DATA_FILES["todos"], todos)

def reminders_page():
    st.header("Reminders")
    reminders = load_json(DATA_FILES["reminders"])
    user_email = st.session_state.user["email"]
    reminder = st.text_input("Reminder Text")
    if st.button("Save Reminder"):
        key = str(len(reminders) + 1)
        reminders[key] = {
            "parent": user_email,
            "reminder": reminder,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["reminders"], reminders)
        st.success("Reminder saved!")

    st.subheader("Your Reminders")
    for r in reminders.values():
        if r["parent"] == user_email:
            st.markdown(f"- {r['reminder']} ({r['timestamp']})")

def documents_page():
    st.header("Document Upload")
    documents = FOLDER_PATHS["documents"]
    uploaded = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])
    if uploaded:
        path = os.path.join(documents, uploaded.name)
        with open(path, "wb") as f:
            f.write(uploaded.read())
        st.success(f"Uploaded {uploaded.name}")

    st.subheader("Uploaded Documents")
    for fname in os.listdir(documents):
        st.markdown(f"- {fname}")

def expenses_page():
    st.header("Expense Tracking")
    expenses = load_json(DATA_FILES["expenses"])
    user_email = st.session_state.user["email"]
    desc = st.text_input("Expense Description")
    amount = st.number_input("Amount", min_value=0.0, step=1.0)
    if st.button("Save Expense"):
        key = str(len(expenses) + 1)
        expenses[key] = {
            "parent": user_email,
            "desc": desc,
            "amount": amount,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["expenses"], expenses)
        st.success("Expense saved!")

    st.subheader("Your Expenses")
    total = 0
    for e in expenses.values():
        if e["parent"] == user_email:
            st.markdown(f"- {e['desc']}: ${e['amount']} ({e['timestamp']})")
            total += e["amount"]
    st.markdown(f"**Total: ${total}**")

def messages_page():
    st.header("Secure Messaging")
    messages = load_json(DATA_FILES["messages"])
    user_email = st.session_state.user["email"]
    msg = st.text_area("Your Message")
    if st.button("Send"):
        key = str(len(messages) + 1)
        messages[key] = {
            "parent": user_email,
            "msg": msg,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["messages"], messages)
        st.success("Message sent!")

    st.subheader("Your Messages")
    for m in messages.values():
        if m["parent"] == user_email:
            st.markdown(f"{m['timestamp']}: {m['msg']}")

def wellness_page():
    st.header("Mental Wellness Check-ins")
    wellness = load_json(DATA_FILES["wellness"])
    user_email = st.session_state.user["email"]
    mood = st.slider("How are you feeling?", 0, 10, 5)
    notes = st.text_area("Notes")
    if st.button("Save Check-in"):
        key = str(len(wellness) + 1)
        wellness[key] = {
            "parent": user_email,
            "mood": mood,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        save_json(DATA_FILES["wellness"], wellness)
        st.success("Check-in saved!")

    st.subheader("Your Check-ins")
    for w in wellness.values():
        if w["parent"] == user_email:
            st.markdown(f"{w['timestamp']}: Mood {w['mood']}")
            st.text(w["notes"])

# ------------------------ Main App ------------------------
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
    elif choice == "Activity Tracking": activity_tracking_page()
    elif choice == "Milestone Tracking": milestone_tracking_page()
    elif choice == "Health Tracking": health_tracking_page()
    elif choice == "To-Do Lists": todos_page()
    elif choice == "Reminders": reminders_page()
    elif choice == "Document Upload": documents_page()
    elif choice == "Expenses": expenses_page()
    elif choice == "Secure Messaging": messages_page()
    elif choice == "Mental Wellness": wellness_page()
    elif choice == "Logout":
        st.session_state.user = None
        st.rerun()

# ------------------------ Main ------------------------
def main():
    st.set_page_config(page_title="Cat’s Cradle", page_icon="🐱", layout="centered")
    
    # Show logo (change path/filename as needed)
    st.image("photos/cats_cradle_logo.png", width=200)
    
    st.title("🐱 Cat’s Cradle")

    if not st.session_state.user:
        auth_choice = st.sidebar.radio("Auth", ["Login", "Register"])
        if auth_choice == "Login":
            login_page()
        else:
            register_page()
    else:
        main_app()

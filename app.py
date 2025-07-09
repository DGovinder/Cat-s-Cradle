import streamlit as st
import json
import os
from PIL import Image
import qrcode

# ------------------------ Config ------------------------
BASE_PATH = "."
USERS_FILE = "users.json"
CHILDREN_FILE = "children.json"
PHOTOS_DIR = "photos"
QRCODES_DIR = "qrcodes"

os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(QRCODES_DIR, exist_ok=True)

LOGO_PATH = os.path.join(PHOTOS_DIR, "cats_cradle_logo.png")

# ------------------------ Utils ------------------------
@st.cache_data
def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

@st.cache_data
def generate_qr_code(child_id, info):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    path = os.path.join(QRCODES_DIR, f"{child_id}.png")
    img.save(path)
    return path

def password_valid(password):
    if len(password) < 6:
        return False
    has_number = any(char.isdigit() for char in password)
    has_special = any(not char.isalnum() for char in password)
    return has_number and has_special

def show_logo():
    if os.path.exists(LOGO_PATH):
        st.image(LOGO_PATH, width=200)
    else:
        st.warning("Logo not found. Please place 'cats_cradle_logo.png' inside the photos/ folder.")

# ------------------------ Session ------------------------
if "user" not in st.session_state:
    st.session_state.user = None
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------------ Auth Pages ------------------------
def register_page():
    st.title("Register")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if not password_valid(password):
            st.error("Password must be at least 6 characters and include numbers and special characters.")
            return
        users = load_json(USERS_FILE)
        if email in users:
            st.error("Email already registered.")
            return
        users[email] = {"full_name": full_name, "password": password}
        save_json(USERS_FILE, users)
        st.success("Registration successful! You can now log in.")

def login_page():
    st.title("Login")
    email = st.text_input("Email").strip().lower()
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_json(USERS_FILE)
        if email in users and users[email]["password"] == password:
            st.session_state.logged_in = True
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
    notes = st.text_area("Notes about the child")
    photo = st.file_uploader("Upload Child Photo", type=["png", "jpg", "jpeg"])

    st.subheader("Add Parent(s) Information")
    parents = []
    for i in range(1, 3):
        with st.expander(f"Parent {i}"):
            p_name = st.text_input(f"Name of Parent {i}", key=f"pname_{i}")
            p_email = st.text_input(f"Email of Parent {i}", key=f"pemail_{i}")
            p_phone = st.text_input(f"Phone of Parent {i}", key=f"pphone_{i}")
            if p_name or p_email or p_phone:
                parents.append({
                    "name": p_name,
                    "email": p_email,
                    "phone": p_phone
                })

    if st.button("Save Child"):
        if not name:
            st.error("Child name is required.")
            return
        if not parents:
            st.error("At least one parent must be added.")
            return

        children = load_json(CHILDREN_FILE)
        child_id = str(len(children) + 1)
        photo_path = ""
        if photo:
            photo_path = os.path.join(PHOTOS_DIR, f"{child_id}_{photo.name}")
            with open(photo_path, "wb") as f:
                f.write(photo.read())

        children[child_id] = {
            "name": name,
            "age": age,
            "notes": notes,
            "photo": photo_path,
            "parents": parents,
            "created_by": st.session_state.user["email"]
        }
        save_json(CHILDREN_FILE, children)

        # Make QR code text
        parent_contacts = "\n".join([
            f"{p['name']} - Email: {p['email']} - Phone: {p['phone']}" for p in parents
        ])
        info = f"I'm lost! My name is {name}.\nParents Contact:\n{parent_contacts}"
        generate_qr_code(child_id, info)

        st.success("Child added successfully!")

def view_children_page():
    st.header("Your Children")
    children = load_json(CHILDREN_FILE)
    user_email = st.session_state.user["email"]
    user_children = {cid: c for cid, c in children.items() if c["created_by"] == user_email}

    if not user_children:
        st.info("You have no children added yet.")
        return

    for cid, child in user_children.items():
        with st.expander(f"{child['name']} (Age {child['age']})"):
            if child["photo"]:
                st.image(child["photo"], width=200)
            st.markdown(f"**Notes:** {child['notes']}")

            st.subheader("Parents Info")
            for i, p in enumerate(child.get("parents", []), start=1):
                st.markdown(f"- **Parent {i}:** {p['name']}")
                st.markdown(f"  - Email: {p['email']}")
                st.markdown(f"  - Phone: {p['phone']}")

            if st.button(f"Show QR Code for {child['name']}", key=f"qr_{cid}"):
                qr_path = os.path.join(QRCODES_DIR, f"{cid}.png")
                if os.path.exists(qr_path):
                    st.image(qr_path)
                else:
                    st.error("QR code not found.")

# ------------------------ Main App ------------------------
def main_app():
    st.sidebar.title(f"Welcome, {st.session_state.user['full_name']}")
    choice = st.sidebar.selectbox("Menu", [
        "Dashboard", "Add Child", "Logout"
    ])

    if choice == "Dashboard":
        view_children_page()
    elif choice == "Add Child":
        add_child_page()
    elif choice == "Logout":
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()

# ------------------------ Main ------------------------
def main():
    st.set_page_config(page_title="Cat’s Cradle", layout="centered")
    show_logo()
    st.title("Cat’s Cradle")

    if not st.session_state.get("logged_in", False):
        auth_choice = st.sidebar.radio("Auth", ["Login", "Register"])
        if auth_choice == "Login":
            login_page()
        else:
            register_page()
    else:
        main_app()

if __name__ == "__main__":
    main()

import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"  # Replace with your backend URL
REGISTER_ENDPOINT = f"{API_BASE_URL}/register"
LOGIN_ENDPOINT = f"{API_BASE_URL}/login"
LOGIN_FACE_ENDPOINT = f"{API_BASE_URL}/login_with_face"

def main():
    apply_custom_style() 
    if "page" not in st.session_state:
        st.session_state.page = "Login"

    # Display sidebar based on user role
    if "role" in st.session_state:
        if st.session_state.role == "admin":
            admin_sidebar()
        else:
            user_sidebar()
    else:
        st.sidebar.title("Navigation")
        st.sidebar.button("Login", on_click=lambda: setattr(st.session_state, "page", "Login"))
        st.sidebar.button("Register", on_click=lambda: setattr(st.session_state, "page", "Register"))

    # Page routing
    if st.session_state.page == "Register":
        register_page()
    elif st.session_state.page == "Login":
        login_page()
    elif st.session_state.page == "Login With Face":
        login_with_face_page()

def apply_custom_style():
    st.markdown(
        """
        <style>
        body {
            background-color: white;
        }

        .st-emotion-cache-15ecox0{
            visibility:hidden;
        }
        /* Button styling */
        button {
            background-color: #f36106 !important; 
            color: white !important;              
            border: none !important;
            border-radius: 5px !important;
            padding: 10px 15px !important;
            font-size: 16px !important;
            cursor: pointer !important;
        }

        /* Button hover effect */
        button:hover {
            background-color: #c25005 !important; 
        }

        /* Sidebar styling */
        .sidebar .sidebar-content {
            background-color: #f8f9fa !important;
        }

        /* Header styling */
        h1, h2, h3, h4, h5, h6 {
            color: #f36106 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
def admin_sidebar():
    st.sidebar.title("Admin Navigation")
    if st.sidebar.button("View Courses", key="admin_dashboard_btn"):
        st.session_state.page = "View Courses"
        st.rerun()
    if st.sidebar.button("Upload Courses", key="admin_upload_btn"):
        st.session_state.page = "Admin Upload"
        st.rerun()
    if st.sidebar.button("Admin Insights", key="admin_insights_btn"):  # New Button
        st.session_state.page = "Admin Insights"
        st.rerun()
    if st.sidebar.button("Log Out", key="admin_logout_btn"):
        logout()

def user_sidebar():
    st.sidebar.title("User Navigation")
    if st.sidebar.button("Pick Interests", key="user_interests_btn"):
        st.session_state.page = "Pick Interests"
        st.rerun()
    if st.sidebar.button("Recommend Courses", key="user_recommend_btn"):
        st.session_state.page = "Recommend Courses"
        st.rerun()
    if st.sidebar.button("Log Out", key="user_logout_btn"):
        logout()

def logout():
    st.session_state.clear()
    st.session_state.page = "Login"
    st.rerun()

def capture_face():
    st.text("Please allow access to your camera")
    try:
        camera_image = st.camera_input("Take a photo")
        
        if camera_image is not None:
            # Convert the captured image to bytes
            face_image = camera_image.getvalue()
            return face_image
        return None
            
    except Exception as e:
        st.error(f"Camera error: {str(e)}")
        return None
    
def register_page():
    st.title("Register")
    
    # Create columns for form and camera
    col1, col2 = st.columns(2)
    
    with col1:
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        phone_number = st.number_input("Phone number")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
    
    with col2:
        st.write("Take a photo for face recognition")
        camera_image = st.camera_input("Camera Input", key="register_camera")
    
    if st.button("Register", key="register_button"):  # Added unique key
        if not all([first_name, last_name, email, password,confirm_password, phone_number, camera_image]):
            st.error("All fields including face photo are required.")
            return
            
        if password != confirm_password:
            st.error("Passwords do not match.")
            return
            
        try:
            files = {
                "face_image": ("face.jpg", camera_image.getvalue(), "image/jpeg")
            }
            
            data = {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "password": password,
                "phone_number": phone_number
            }
            
            with st.spinner("Registering..."):
                st.write("Sending registration request...")
                response = requests.post(
                    REGISTER_ENDPOINT,
                    data=data,
                    files=files
                )
                
                st.write(f"Response status code: {response.status_code}")
                
                if response.status_code == 201:
                    st.success("Registration successful! Please login.")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    error_detail = response.json().get("detail", "Registration failed.")
                    st.error(f"Registration failed: {error_detail}")
                    st.write(f"Full response: {response.text}")
                    
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
    
    if st.button("Go to Login", key="goto_login_button"): 
        st.session_state.page = "Login"
        st.rerun()

# Login with face recognition
def login_with_face_page():
    st.title("Login with Face Recognition")
    
    face_image = capture_face()
    
    if face_image is not None:
        if st.button("Login with this photo"):
            files = {"face_image": ("face.jpg", face_image, "image/jpeg")}
            try:
                response = requests.post(LOGIN_FACE_ENDPOINT, files=files)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data.get("token")
                    st.session_state.role = data.get("role", "user")
                    st.success("Login successful!")

                    if st.session_state.role == "admin":
                        st.session_state.page = "Admin Dashboard"
                    else:
                        st.session_state.page = "Pick Interests"
                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Login failed."))
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    
    if st.button("Back to Login"):
        st.session_state.page = "Login"
        st.rerun()


                
def login_page():
    st.title("Login")

    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

        if submit:
            try:
                response = requests.post(LOGIN_ENDPOINT, json={"email": email, "password": password})
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.token = data.get("token")
                    st.session_state.role = data.get("role", "user")  # Default to "user" if role is not provided
                    st.success("Login successful!")

                    if st.session_state.role == "admin":
                        print(st.session_state.role)
                        st.session_state.page = "Admin Dashboard"
                        st.rerun()
                    else:
                        st.session_state.page = "Pick Interests"
                        st.rerun()
                else:
                    error_msg = response.json().get("detail", "Login failed.")
                    st.error(error_msg)
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")

    if st.button("Register", key="register_button"):
        st.session_state.page = "Register"
        st.rerun()
    if st.button("Login With Face", key="login_face_button"):
        st.session_state.page = "Login With Face"
        st.rerun()
<<<<<<< HEAD
if __name__ =="__main__":
=======
if __name__ == "__main__":
>>>>>>> 2244b9f48352d5520e417851783346d7294b313a
    main()
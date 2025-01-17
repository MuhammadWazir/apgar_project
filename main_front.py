import streamlit as st
import requests
import time
import pandas as pd
import matplotlib.pyplot as plt

API_BASE_URL = "http://localhost:8000"
REGISTER_ENDPOINT = f"{API_BASE_URL}/register"
LOGIN_ENDPOINT = f"{API_BASE_URL}/login"
INTERESTS_ENDPOINT = f"{API_BASE_URL}/interests"
COURSES_ENDPOINT = f"{API_BASE_URL}/courses"
UPLOAD_COURSES_ENDPOINT = f"{API_BASE_URL}/upload-courses-pdf"
LOGIN_FACE_ENDPOINT = f"{API_BASE_URL}/login_with_face"

COURSES_ENDPOINT = f"{API_BASE_URL}/courses"

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
    elif st.session_state.page == "Pick Interests":
       interests_page()
    elif st.session_state.page == "Recommend Courses":
       recommend_courses_page()
    elif st.session_state.page == "View Courses":
        admin_dashboard_page()
    elif st.session_state.page == "Admin Upload":
        admin_upload_page()
    elif st.session_state.page == "Pick Interests":
        interests_page()
    elif st.session_state.page == "Recommend Courses":
        recommend_courses_page()
    elif st.session_state.page == "Admin Insights":  
        admin_insights_page()

def apply_custom_style():
    st.markdown(
        """
        <style>
        /* Global styles */
        body {
            background-color: white;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
        }

        .st-emotion-cache-15ecox0 {
            visibility: hidden;
        }

        /* Button styling with improved aesthetics */
        button {
            background-color: #f36106 !important;
            color: white !important;
            border: none !important;
            border-radius: 8px !important;
            padding: 12px 20px !important;
            font-size: 16px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(243, 97, 6, 0.2) !important;
            font-weight: 500 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }

        button:hover {
            background-color: #c25005 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 8px rgba(243, 97, 6, 0.3) !important;
        }

        button:active {
            transform: translateY(0) !important;
            box-shadow: 0 2px 4px rgba(243, 97, 6, 0.2) !important;
        }

        /* Sidebar improvements */
        .sidebar .sidebar-content {
            background-color: #f8f9fa !important;
            border-right: 1px solid #e9ecef !important;
            padding: 20px !important;
        }

        .sidebar button {
            background-color: #f8f9fa !important;
            border: 1px solid #e9ecef !important;
            margin: 5px 0 !important;
            width: 100% !important;
            text-align: left !important;
        }

        /* Header styling with better hierarchy */
        h1 {
            color: #f36106 !important;
            font-size: 2.5em !important;
            font-weight: 700 !important;
            margin-bottom: 0.5em !important;
            border-bottom: 3px solid rgba(243, 97, 6, 0.2) !important;
            padding-bottom: 0.2em !important;
        }

        h2 {
            color: #f36106 !important;
            font-size: 2em !important;
            font-weight: 600 !important;
            margin: 1em 0 0.5em 0 !important;
        }

        h3 {
            color: #f36106 !important;
            font-size: 1.5em !important;
            font-weight: 600 !important;
            margin: 0.8em 0 0.4em 0 !important;
        }

        /* Input fields styling */
        .stTextInput input, .stSelectbox select {
            border-radius: 6px !important;
            border: 1px solid #e0e0e0 !important;
            padding: 8px 12px !important;
            transition: all 0.3s ease !important;
        }

        .stTextInput input:focus, .stSelectbox select:focus {
            border-color: #f36106 !important;
            box-shadow: 0 0 0 2px rgba(243, 97, 6, 0.2) !important;
        }

        /* Progress bars and metrics */
        .stProgress > div > div {
            background-color: rgba(243, 97, 6, 0.2) !important;
        }

        .stProgress > div > div > div {
            background-color: #f36106 !important;
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
        phone_number = st.text_input("Phone number")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
    
    with col2:
        st.write("Take a photo for face recognition")
        camera_image = st.camera_input("Camera Input", key="register_camera")
    
    if st.button("Register", key="register_button"):  # Added unique key
        if not all([first_name, last_name, email, password, confirm_password, phone_number, camera_image]):
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
                response = requests.post(
                    REGISTER_ENDPOINT,
                    data=data,
                    files=files
                )
                st.write("Response status code:", response.status_code)
                st.write("Response content:", response.content)
                if response.status_code == 201:
                    st.success("Registration successful! Please login.")
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    try:
                        error_response = response.json()
                        if "Email verification failed" in error_response.get("detail", ""):
                            st.error("""
                                Email verification failed. Please ensure:
                                - You've entered the email correctly
                                - The email domain exists
                                - The email address is valid and active
                                Try using a different email address or contact support if the issue persists.
                            """)
                        else:
                            st.error(f"Registration failed: {error_response.get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Registration failed: Unable to process server response")
                    
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

        
def interests_page():
    st.title("Pick Interests")
    if "token" not in st.session_state:
        st.error("You must be logged in to access this page.")
        st.session_state.page = "Login"
        return

    with st.form("interests_form"):
        interests = st.multiselect(
            "Select your interests:",
            ["Project Managment", "Machine Learning", "Data Science", "Web Development", "Mobile Development", "AI",
             "Career Switch to Tech",
                "Skill Enhancement",
                "Personal Project",
                "Academic Research",
                "Professional Development",
                "Starting a Tech Business",
                "Cybersecurity",
                "Blockchain",
                "Internet of Things (IoT)",
                "Game Development",
                "UI/UX Design",
                "Embedded Systems",
                "AR/VR Development",
                "Quantum Computing",
                "Python",
                "JavaScript",
                "Java",
                "C++",
                "Go",
                "Rust",
                "TypeScript",
                "SQL",
                "Web Development",
                "Mobile App Development",
                "Backend Development",
                "Frontend Development",
                "Full Stack Development",
                "API Development",
                "DevOps",
                "Cloud Computing"
            ]
        )

        submit = st.form_submit_button("Save Interests")

        if submit:
            response = requests.post(INTERESTS_ENDPOINT, json={"interests": interests}, headers={
                "Authorization": f"Bearer {st.session_state.token}"
            })

            if response.status_code == 200:
                st.success("Interests saved successfully!")
                st.session_state.page = "Recommend Courses"
                st.rerun()
            else:
                st.error(response.json().get("detail", "Failed to save interests."))


def admin_upload_page():
    st.title("Admin Dashboard")

    if "token" not in st.session_state or st.session_state.get("role") != "admin":
        st.error("Access denied. You must be an admin to view this page.")
        st.session_state.page = "Login"
        return

    st.write("Welcome, Admin!")
    
    # PDF Upload Section
    st.subheader("Upload PDF for Processing")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])

    if uploaded_file is not None:
        try:
            # Preview request
            preview_response = requests.post(
                f"{API_BASE_URL}/preview-courses-pdf",
                headers={"Authorization": f"Bearer {st.session_state.token}"},
                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
            )

            if preview_response.status_code == 200:
                courses = preview_response.json()["courses"]
                
                # Main content area
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    if len(courses) > 0:
                        st.subheader(f"Found {len(courses)} Courses")
                        for i, course in enumerate(courses, 1):
                            st.markdown(f"""
                            **Course {i}: {course['title']}**
                            - **Description:** {course['description']}
                            - **Schedule:** {course['schedule']}
                            ---
                            """)
                    else:
                        st.error("No courses were found in the PDF.")
                        st.markdown("### PDF Content Preview")
                        st.text(preview_response.json().get("debug_info", {}).get("raw_text", "No content available"))
                
                with col2:
                    if len(courses) > 0:
                        if st.button("Confirm Upload"):
                            upload_response = requests.post(
                                f"{API_BASE_URL}/upload-courses-pdf",
                                headers={"Authorization": f"Bearer {st.session_state.token}"},
                                files={"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")},
                            )

                            if upload_response.status_code == 200:
                                st.success("Courses uploaded successfully!")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Failed to upload courses.")
                
            else:
                st.error("Failed to preview PDF content.")
                
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")

    # Logout button at the bottom
    st.button("Log Out", on_click=lambda: setattr(st.session_state, "page", "Login"))

    
def admin_dashboard_page():
    st.title("Admin Dashboard")

    if "token" not in st.session_state or st.session_state.get("role") != "admin":
        st.error("Access denied. You must be an admin to view this page.")
        st.session_state.page = "Login"
        return

    st.write("Welcome, Admin!")

    # Fetch and display all courses
    st.subheader("Manage Courses")
    try:
        response = requests.get(
            f"{API_BASE_URL}/courses/all", 
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if response.status_code == 200:
            courses = response.json()
            if not courses:
                st.info("No courses available.")
            else:
                for course in courses:
                    with st.expander(f"📘 {course['title']}"):
                        st.write(f"**Description:** {course['description']}")
                        # Assign unique key for each button
                        if st.button(f"Delete {course['title']}", key=f"delete_{course['id']}"):
                            delete_response = requests.delete(
                                f"{API_BASE_URL}/courses/{course['id']}",
                                headers={"Authorization": f"Bearer {st.session_state.token}"}
                            )
                            if delete_response.status_code == 200:
                                st.success(f"Course '{course['title']}' deleted successfully!")
                                st.rerun()
                            else:
                                st.error(delete_response.json().get("detail", "Failed to delete course."))
        else:
            st.error(response.json().get("detail", "Failed to fetch courses."))
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")

def admin_insights_page():
    st.title("Admin Insights")

    if "token" not in st.session_state or st.session_state.get("role") != "admin":
        st.error("Access denied. You must be an admin to view this page.")
        st.session_state.page = "Login"
        return

    # Fetch interest stats
    st.subheader("Interest Statistics")
    try:
        interest_response = requests.get(
            f"{API_BASE_URL}/admin/interest_stats", 
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if interest_response.status_code == 200:
            interest_data = interest_response.json()
            if interest_data:
                # Convert to DataFrame
                interest_df = pd.DataFrame(interest_data)
                
                # Bar plot for interest stats
                fig, ax = plt.subplots()
                ax.bar(interest_df['interest'], interest_df['count'], color='skyblue')
                ax.set_title("Interest Category Frequencies")
                ax.set_xlabel("Interests")
                ax.set_ylabel("Frequency")
                ax.set_xticks(range(len(interest_df['interest'])))
                ax.set_xticklabels(interest_df['interest'], rotation=45, ha='right')
                
                st.pyplot(fig)
            else:
                st.info("No interest data available.")
        else:
            st.error(interest_response.json().get("detail", "Failed to fetch interest statistics."))
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")

    # Fetch recommendation stats
    st.subheader("Recommendation Statistics")
    try:
        recommendation_response = requests.get(
            f"{API_BASE_URL}/admin/recommendation_stats", 
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )
        if recommendation_response.status_code == 200:
            recommendation_data = recommendation_response.json()
            if recommendation_data:
                # Convert to DataFrame
                recommendation_df = pd.DataFrame(recommendation_data)

                # Bar plot for recommendation stats
                fig, ax = plt.subplots()
                ax.bar(recommendation_df['course_title'], recommendation_df['count'], color='lightcoral')
                ax.set_title("Recommendation Frequencies by Course")
                ax.set_xlabel("Courses")
                ax.set_ylabel("Frequency")
                ax.set_xticks(range(len(recommendation_df['course_title'])))
                ax.set_xticklabels(recommendation_df['course_title'], rotation=45, ha='right')
                
                st.pyplot(fig)
            else:
                st.info("No recommendation data available.")
        else:
            st.error(recommendation_response.json().get("detail", "Failed to fetch recommendation statistics."))
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")

def recommend_courses_page():
    st.title("Recommended Courses")

    if "token" not in st.session_state:
        st.error("You must be logged in to access this page.")
        st.session_state.page = "Login"
        return

    try:
        response = requests.get(
            COURSES_ENDPOINT, 
            headers={"Authorization": f"Bearer {st.session_state.token}"}
        )

        # Check if response is successful and contains content
        if response.status_code == 200:
            try:
                data = response.json()
                courses = data.get("courses", [])
                
                if courses:
                    st.write("Here are some recommended courses based on your interests:")
                    
                    # Create columns for better layout
                    for course in courses:
                        with st.expander(f"📚 {course['title']} - Match Score: {course['similarity_score']}"):
                            st.write(f"**title:** {course['title']}")
                            st.write(f"**Description:** {course['description']}")
                            st.write(f"**Schedule:** {course['schedule']}")
                            # Add a visual indicator for similarity score
                            score = float(course['similarity_score'])
                            st.progress(score)
                        
                else:
                    st.info("No courses match your interests at this time. Try updating your interests!")
                    
                    # Add a button to update interests
                    if st.button("Update Interests"):
                        st.session_state.page = "Pick Interests"
                        st.rerun()
            
            except requests.exceptions.JSONDecodeError:
                st.error("Error parsing the server response. Please try again later.")
                
        elif response.status_code == 401:
            st.error("Your session has expired. Please log in again.")
            st.session_state.page = "Login"
            st.rerun()
            
        elif response.status_code == 404:
            st.warning("The course recommendation service is currently unavailable.")
            
        else:
            try:
                error_msg = response.json().get("detail", "An unknown error occurred.")
                st.error(f"Error: {error_msg}")
            except:
                st.error(f"Error: Server returned status code {response.status_code}")
                
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to the server: {str(e)}")

    # Add logout button with confirmation
    if st.button("Log Out"):
        if st.button("Confirm Logout"):
            st.session_state.clear()
            st.session_state.page = "Login"
            st.rerun()
if __name__ == "__main__":
    main()

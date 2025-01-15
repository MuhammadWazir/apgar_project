from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from typing import List
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from dotenv import load_dotenv
import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import EmailStr
import spacy
import requests
import PyPDF2
import io
import re
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from sqlalchemy.orm import relationship, Session
import spacy


import face_recognition
import numpy as np
from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from typing import Optional
import io
from PIL import Image

from create_db import Course, User, Interest, RecommendedCourse

# Database setup - Using existing rec.db
SQLALCHEMY_DATABASE_URL = "sqlite:///./rec.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# JWT settings
SECRET_KEY = "12345"  # In production, use a secure secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")
# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Pydantic models for request/response
class UserCreate(BaseModel):
    first_name: str
    last_name: str
    phone_number: str
    email: str
    password: str
    

class UserLogin(BaseModel):
    email: str
    password: str

class InterestUpdate(BaseModel):
    interests: List[str]

class Token(BaseModel):
    token: str

# Helper functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_email_with_hunter(email: str) -> dict:
    url = f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={HUNTER_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid Hunter API key.")
    elif response.status_code == 429:
        raise HTTPException(status_code=429, detail="Hunter API rate limit exceeded.")
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Create FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conf = ConnectionConfig(
    MAIL_USERNAME="muhammad.elwazir@lau.edu",
    MAIL_PASSWORD="mW24mW24mW24/", 
    MAIL_FROM="muhammad.elwazir@lau.edu",
    MAIL_PORT=587,
    MAIL_SERVER="outlook.office365.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)
# Endpoints
@app.post("/register", status_code=201)
async def register(
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone_number: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Verify email using Hunter API
    try:
        email_verification_result = verify_email_with_hunter(email)
        if email_verification_result.get("data", {}).get("result") != "deliverable":
            raise HTTPException(status_code=400, detail="Invalid or undeliverable email.")
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email verification failed: {str(e)}")

    # Check if email already exists
    db_user = db.query(User).filter(User.email == email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    # Process the face image
    try:
        contents = await face_image.read()
        image = Image.open(io.BytesIO(contents))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_np = np.array(image)
        face_locations = face_recognition.face_locations(image_np)
        if len(face_locations) != 1:
            raise HTTPException(status_code=400, detail="Invalid face image: Please ensure one face is visible.")
        face_signature = face_recognition.face_encodings(image_np, face_locations)[0]

        # Check if face is already registered
        existing_users = db.query(User).filter(User.face_signature.isnot(None)).all()
        for existing_user in existing_users:
            existing_encoding = np.frombuffer(existing_user.face_signature)
            if face_recognition.compare_faces([existing_encoding], face_signature)[0]:
                raise HTTPException(status_code=400, detail="This face is already registered.")

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            firstname=first_name,
            lastname=last_name,
            phone=phone_number,
            email=email,
            hashed_password=hashed_password,
            face_signature=face_signature.tobytes()
        )
        db.add(new_user)
        db.commit()

        return {"message": "User registered successfully."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Face processing failed: {str(e)}")

@app.post("/login")
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    print(f"Login attempt for email: {user_credentials.email}")  # Debug print
    try:
        # Fetch user from the database
        user = db.query(User).filter(User.email == user_credentials.email).first()
        print(f"User found: {user is not None}")  # Debug print
        
        if not user:
            print("No user found with this email")  # Debug print
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        
        valid_password = verify_password(user_credentials.password, user.hashed_password)
        
        if not valid_password:
            raise HTTPException(
                status_code=401,
                detail="Incorrect email or password"
            )
        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        message = MessageSchema(
            subject="Login Notification",
            recipients=[user.email],
            body=f"Hi {user.firstname}, you just logged into your account.",
            subtype="plain"
        )
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
            print("Sent")
        except Exception as e:
            print(f"Error sending email: {e}") 
            raise HTTPException(status_code=500, detail="Failed to send email")


        return {"token": access_token, "role": user.role, "status": "success"}
    
    except Exception as e:
        print(f"Error during login: {str(e)}")  # Debug print
        raise HTTPException(
            status_code=500,
            detail="An error occurred during login. Please try again later."
        )


@app.post("/login_with_face")
async def login_with_face(
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Read and process the uploaded image
        contents = await face_image.read()
        image = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array
        image_np = np.array(image)
        
        # Detect face in the image
        face_locations = face_recognition.face_locations(image_np)
        if not face_locations:
            raise HTTPException(
                status_code=400,
                detail="No face detected in the image"
            )
        
        # Get face encoding from login image
        login_face_encoding = face_recognition.face_encodings(image_np, face_locations)[0]
        
        # Get all users with face encodings
        users = db.query(User).filter(User.face_signature.isnot(None)).all()
        
        # Check against all stored face encodings
        for user in users:
            stored_encoding = np.frombuffer(user.face_signature)
            match = face_recognition.compare_faces(
                [stored_encoding], 
                login_face_encoding,
                tolerance=0.6
            )[0]
            
            if match:
                # Create access token
                access_token = create_access_token(
                    data={"sub": user.email, "role": user.role}
                )
                
                return {
                    "token": access_token,
                    "role": user.role,
                    "status": "success"
                }
        
        # If no match found
        raise HTTPException(
            status_code=401,
            detail="Face not recognized"
        )
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during face login: {str(e)}"
        )


# ---------------------------------------------------------------------------------------

def update_user_recommendations(db: Session, user_id: int):
    nlp = spacy.load("en_core_web_lg")
    
    # Get user and their interests
    user = db.query(User).filter(User.id == user_id).first()
    user_interests = [interest.interest for interest in user.interests]
    interest_docs = [nlp(interest.lower()) for interest in user_interests]
    
    # Clear existing recommendations
    db.query(RecommendedCourse).filter(RecommendedCourse.user_id == user_id).delete()
    
    # Get all courses
    all_courses = db.query(Course).all()
    
    # Calculate new recommendations
    new_recommendations = []
    for course in all_courses:
        course_text = f"{course.category} {course.description}"
        course_doc = nlp(course_text.lower())
        
        similarity_scores = [
            course_doc.similarity(interest_doc)
            for interest_doc in interest_docs
        ]
        
        max_similarity = max(similarity_scores) if similarity_scores else 0
        
        if max_similarity >= 0.8:
            recommendation = RecommendedCourse(
                user_id=user_id,
                course_id=course.id,
                similarity_score=max_similarity
            )
            new_recommendations.append(recommendation)
    
    # Add new recommendations to database
    db.bulk_save_objects(new_recommendations)
    db.commit()


@app.post("/interests")
async def update_interests(
    interests_update: InterestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Clear existing interests
    db.query(Interest).filter(Interest.user_id == current_user.id).delete()
    
    # Add new interests
    for interest in interests_update.interests:
        db_interest = Interest(interest=interest, user_id=current_user.id)
        db.add(db_interest)
    
    db.commit()
    
    # Update recommendations explicitly after deleting interests
    update_user_recommendations(db, current_user.id)
    
    return {"message": "Interests updated successfully"}

# Modified course recommendation endpoint
@app.get("/courses")
async def get_recommended_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    recommended_courses = (
        db.query(RecommendedCourse)
        .filter(RecommendedCourse.user_id == current_user.id)
        .order_by(RecommendedCourse.similarity_score.desc())
        .all()
    )
    
    return {
        "courses": [
            {
                "title": rec.course.title,
                "category": rec.course.category,
                "description": rec.course.description,
                "similarity_score": round(rec.similarity_score, 2)
            }
            for rec in recommended_courses
        ]
    }




# @app.post("/interests")
# async def update_interests(
#     interests_update: InterestUpdate,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     # Clear existing interests
#     db.query(Interest).filter(Interest.user_id == current_user.id).delete()
    
#     # Add new interests
#     for interest in interests_update.interests:
#         db_interest = Interest(interest=interest, user_id=current_user.id)
#         db.add(db_interest)
    
#     db.commit()
#     return {"message": "Interests updated successfully"}



# @app.get("/courses")
# async def get_recommended_courses(
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     nlp = spacy.load("en_core_web_lg")
#     # Get user interests
#     user_interests = [interest.interest for interest in current_user.interests]
    
#     # Process user interests with spaCy
#     interest_docs = [nlp(interest.lower()) for interest in user_interests]
    
#     # Get all courses from database
#     all_courses = db.query(Course).all()
#     recommended_courses = []
    
#     for course in all_courses:
#         # Combine category and description for better matching
#         course_text = f"{course.category} {course.description}"
#         course_doc = nlp(course_text.lower())
        
#         # Calculate similarity scores for each user interest
#         similarity_scores = [
#             course_doc.similarity(interest_doc)
#             for interest_doc in interest_docs
#         ]
        
#         # Get the maximum similarity score
#         max_similarity = max(similarity_scores)
        
#         # If similarity score is above threshold, add course to recommendations
#         if max_similarity >= 0.8:
#             recommended_courses.append({
#                 "course": course,
#                 "similarity_score": max_similarity
#             })
    
#     # Sort recommendations by similarity score in descending order
#     recommended_courses.sort(key=lambda x: x["similarity_score"], reverse=True)
    
#     return {
#         "courses": [
#             {
#                 "title": rec["course"].title,
#                 "category": rec["course"].category,
#                 "description": rec["course"].description,
#                 "similarity_score": round(rec["similarity_score"], 2)
#             }
#             for rec in recommended_courses
#         ]
#     }

# Helper function to analyze course content
def analyze_course_content(course_text: str) -> dict:
    """
    Analyze course content to extract key terms and themes
    """
    nlp = spacy.load('en_core_web_lg')
    doc = nlp(course_text.lower())
    
    # Extract key noun phrases and entities
    key_terms = []
    
    for chunk in doc.noun_chunks:
        if not chunk.root.is_stop:
            key_terms.append(chunk.text)
    
    for ent in doc.ents:
        key_terms.append(ent.text)
    
    # Remove duplicates and sort
    key_terms = list(set(key_terms))
    
    return {
        "key_terms": key_terms,
        "processed_text": " ".join([token.text for token in doc if not token.is_stop])
    }


# ------------------------------------------------------------------------------------------


def extract_course_info(pdf_content: bytes) -> dict:
    """Extract course information from PDF content."""
    pdf_file = io.BytesIO(pdf_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    # Extract text from first page
    text = pdf_reader.pages[0].extract_text()
    
    # Extract title (first line of the PDF)
    title_pattern = r'^(.+?)(?:\n|$)'
    title_match = re.search(title_pattern, text)
    title = title_match.group(1).strip() if title_match else "Unknown Title"
    
    # Extract category (looking for "Core Areas" or similar section headers)
    categories = []
    category_pattern = r'Core Areas.*?(?:\n|:)\s*(.*?)(?:\n\d|\n\n|$)'
    category_match = re.search(category_pattern, text, re.DOTALL)
    if category_match:
        category_text = category_match.group(1)
        categories = [cat.strip() for cat in category_text.split('\n') if cat.strip()]
    category = categories[0] if categories else "General Engineering"
    
    # Extract description (text between title and core areas)
    description_pattern = r'{}\s*(.*?)(?:Core Areas|Applications|Skills Required)'.format(re.escape(title))
    description_match = re.search(description_pattern, text, re.DOTALL)
    description = description_match.group(1).strip() if description_match else "No description available"
    
    return {
        "title": title,
        "category": category,
        "description": description
    }




@app.post("/upload-courses-pdf/")
async def upload_courses(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint to handle PDF upload and process course information
    """
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can upload courses")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Read file content
        content = await file.read()
        
        # Extract course information
        course_info = extract_course_info(content)
        
        # Create new course in database
        new_course = Course(
            title=course_info["title"],
            category=course_info["category"],
            description=course_info["description"]
        )
        
        # Add to database
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        return {
            "message": "Course added successfully",
            "course": {
                "title": new_course.title,
                "category": new_course.category,
                "description": new_course.description
            }
        }
        
    except PyPDF2.PdfReadError:
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")
    finally:
        await file.close()

@app.get("/courses/all", response_model=List[dict])
async def get_all_courses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can access this resource.")

    courses = db.query(Course).all()
    return [{"id": course.id, "title": course.title, "category": course.category, "description": course.description} for course in courses]

@app.delete("/courses/{course_id}")
async def delete_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete courses.")

    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    db.delete(course)
    db.commit()
    return {"message": f"Course '{course.title}' deleted successfully."}

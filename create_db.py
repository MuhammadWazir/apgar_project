from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, ForeignKey
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from passlib.context import CryptContext

from sqlalchemy import LargeBinary
from sqlalchemy.orm import relationship

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./rec.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String)
    lastname = Column(String)
    phone = Column(String)
    email = Column(String, unique=True, index=True)
    face_signature = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)  
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    hashed_password = Column(String)
    role = Column(String, default="user")
    interests = relationship("Interest", back_populates="user")

class Interest(Base):
    __tablename__ = "interests"
    id = Column(Integer, primary_key=True, index=True)
    interest = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="interests")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)


class RecommendedCourse(Base):
    __tablename__ = "recommended_courses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))
    similarity_score = Column(Float)
    
    user = relationship("User", backref="recommended_courses")
    course = relationship("Course")

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize sample courses
def initialize_sample_data():
    db = SessionLocal()
    
 
        
    # Add a sample users
    sample_user_admin = User(
        firstname="admin",
        lastname="admin",
        phone= "123",
        email="admin@gmail.com",
        hashed_password=pwd_context.hash("admin"),
        role="admin"
    )
    db.add(sample_user_admin)

    sample_user = User(
        firstname="user",
        lastname="user",
        phone= "123",
        email="user@gmail.com",
        hashed_password=pwd_context.hash("user"),
        role="user"
    )
    db.add(sample_user)
    
    # Commit the changes
    db.commit()
    print("Sample data initialized successfully!")

    db.close()

if __name__ == "__main__":
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    print("Initializing sample data...")
    initialize_sample_data()
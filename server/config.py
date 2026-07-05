import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class Config:
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:your_password@localhost:5432/apollo_tyres')
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-this')
    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60))
    
    # Abaqus
    ABQ_EXE = os.getenv('ABQ_EXE', 'D:/SIMULIA/Commands/abaqus.bat')
    ABQ_CPUS = int(os.getenv('ABQ_CPUS', 1))
    ABQ_ASK_DEL = os.getenv('ABQ_ASK_DEL', 'no')
    
    # Paths
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    PROJECTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'projects')
    PROTOCOL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'protocol')
    
    # Cors
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')

config = Config()
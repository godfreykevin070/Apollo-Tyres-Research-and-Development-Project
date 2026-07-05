import asyncio
from database import db
from auth import get_password_hash
from utils.helpers import generate_unique_id

async def create_initial_user():
    await db.connect()
    
    # Check if admin exists
    existing = await db.execute_one(
        "SELECT id FROM users WHERE email = $1",
        "admin@apollotyres.com"
    )
    
    if existing:
        print("Admin user already exists")
        return
    
    # Create admin user
    user_id = generate_unique_id("USR")
    hashed_password = get_password_hash("Admin@123")
    
    result = await db.execute_one(
        """
        INSERT INTO users (id, email, password, name, role, created_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
        RETURNING id, email, name, role
        """,
        user_id, "admin@apollotyres.com", hashed_password, "Admin", "admin"
    )
    
    print(f"Admin user created: {dict(result)}")

if __name__ == "__main__":
    asyncio.run(create_initial_user())
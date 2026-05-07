import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse as urlparse
from urllib.parse import urlencode

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# For asyncpg, we need to ensure the driver is specified and clean the URL
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Clean the URL from parameters that asyncpg doesn't like (sslmode, channel_binding)
    if "?" in DATABASE_URL:
        url_parts = list(urlparse.urlparse(DATABASE_URL))
        query = dict(urlparse.parse_qsl(url_parts[4]))
        
        # Check if we need SSL
        use_ssl = query.get('sslmode') == 'require' or 'sslmode' in query
        
        # Remove incompatible keys
        query.pop('sslmode', None)
        query.pop('channel_binding', None)
        
        url_parts[4] = urlencode(query)
        DATABASE_URL = urlparse.urlunparse(url_parts)

engine = create_async_engine(
    DATABASE_URL, 
    echo=False,
    connect_args={"ssl": True} # Neon requires SSL
)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_or_create_user(telegram_id: int, username: str = None):
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(telegram_id=telegram_id, username=username)
            session.add(user)
            await session.commit()
        return user

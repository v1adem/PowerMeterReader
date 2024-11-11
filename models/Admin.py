from sqlalchemy import Column, Integer, String

from config import Base


class Admin(Base):
    __tablename__ = 'admin'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=1)

    def __repr__(self):
        return f"<Admin(username='{self.username}')>"

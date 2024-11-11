from sqlalchemy import Column, Integer, String
from config import Base


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', description='{self.description}')>"

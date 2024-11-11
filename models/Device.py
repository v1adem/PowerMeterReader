from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from config import Base


class Device(Base):
    __tablename__ = 'devices'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    name = Column(String, nullable=False, unique=True)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    device_address = Column(Integer, nullable=False)
    baudrate = Column(Integer, nullable=False, default=9600)
    bytesize = Column(Integer, nullable=False, default=8)
    stopbits = Column(Integer, nullable=False, default=1)
    parity = Column(String, nullable=False, default='N')

    reading_type = Column(Integer, nullable=False, default=1)  # 1 for interval, 2 for time
    reading_interval = Column(Integer, nullable=False, default=3600)
    reading_time = Column(Float, nullable=False, default=0)

    # String with parameters to read in format {Parameter1:Units1, Parameter2:Units2,...,ParameterN:UnitsN}
    parameters = Column(String, nullable=False, default="Voltage:V,Current:A,Power:W")

    project = relationship("Project")

    def __repr__(self):
        return (f"<Device(id={self.id}, name='{self.name}', manufacturer='{self.manufacturer}', "
                f"model='{self.model}', device_address={self.device_address}, project_id={self.project_id})>")

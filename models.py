from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    plate = Column(String, primary_key=True, index=True)
    type = Column(String, default="Automobile")
    last_seen = Column(String)
    
    violations = relationship("Violation", back_populates="vehicle_rel")

class Violation(Base):
    __tablename__ = "violations"
    
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    plate = Column(String, ForeignKey("vehicles.plate"))
    type = Column(String, nullable=False) # e.g. HELMET_NON_COMPLIANCE
    vehicle = Column(String, default="Automobile")
    risk_score = Column(Integer, default=0)
    confidence = Column(String, default="90%")
    fine = Column(String, default="$150.00")
    status = Column(String, default="PENDING_REVIEW") # APPROVED, PENDING_REVIEW, DISMISSED
    
    vehicle_rel = relationship("Vehicle", back_populates="violations")
    evidence = relationship("Evidence", back_populates="violation", cascade="all, delete-orphan")

class Offender(Base):
    __tablename__ = "offenders"
    
    plate = Column(String, ForeignKey("vehicles.plate"), primary_key=True)
    violations_count = Column(Integer, default=1)
    risk_average = Column(Float, default=0.0)

class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(String, primary_key=True, index=True)
    violation_id = Column(String, ForeignKey("violations.id", ondelete="CASCADE"))
    annotated_image_path = Column(String)
    pdf_path = Column(String)
    metadata_json = Column(Text) # JSON string representation
    
    violation = relationship("Violation", back_populates="evidence")

class Junction(Base):
    __tablename__ = "junctions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    base_risk_score = Column(Integer, default=50)

class Hotspot(Base):
    __tablename__ = "hotspots"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    junction_name = Column(String, ForeignKey("junctions.name"))
    predicted_risk = Column(Integer, default=50)
    peak_hours = Column(String)
    patrol_count = Column(Integer, default=1)

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    junction_name = Column(String, ForeignKey("junctions.name"))
    hour = Column(Integer) # 0 to 23
    predicted_violations = Column(Float, default=0.0)
    recommendation = Column(String)

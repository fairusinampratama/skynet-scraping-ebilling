from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Area(Base):
    __tablename__ = "areas"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), nullable=True)
    name = Column(String(255), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customers = relationship("Customer", back_populates="area")


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    price = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customers = relationship("Customer", back_populates="package")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(50), primary_key=True, index=True)  # id_pelanggan
    code = Column(String(50), nullable=True)
    name = Column(String(255), nullable=True)
    nik = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    
    geo_lat = Column(Numeric(10, 8), nullable=True)
    geo_long = Column(Numeric(11, 8), nullable=True)
    
    pppoe_user = Column(String(100), nullable=True)
    pppoe_password = Column(String(100), nullable=True)
    
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=True)
    area_id = Column(Integer, ForeignKey("areas.id"), nullable=True)
    
    status = Column(String(50), nullable=True)
    join_date = Column(Date, nullable=True)
    due_day = Column(Integer, nullable=True)
    ktp_photo_url = Column(Text, nullable=True)
    is_online = Column(Boolean, default=False)
    
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    package = relationship("Package", back_populates="customers")
    area = relationship("Area", back_populates="customers")
    invoices = relationship("Invoice", back_populates="customer")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True)
    customer_id = Column(String(50), ForeignKey("customers.id"))
    code = Column(String(50), nullable=True)
    period = Column(Date, nullable=True)
    amount = Column(Numeric(10, 2), default=0)
    status = Column(String(50), nullable=True)
    due_date = Column(Date, nullable=True)
    generated_at = Column(DateTime, nullable=True)
    payment_link = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="invoices")


class Branch(Base):
    __tablename__ = "branches"

    cabang = Column(String(100), primary_key=True, index=True)
    jumlah_pelanggan = Column(Integer, default=0)
    pelanggan_lunas = Column(Integer, default=0)
    pelanggan_belum_lunas = Column(Integer, default=0)
    total_pemasukan = Column(Numeric(15, 2), default=0)
    total_pengeluaran = Column(Numeric(15, 2), default=0)
    balance = Column(Numeric(15, 2), default=0)
    total_estimasi = Column(Numeric(15, 2), default=0)
    last_synced_at = Column(DateTime, default=datetime.utcnow)


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True) # success, partial, failed
    customers_synced = Column(Integer, default=0)
    invoices_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

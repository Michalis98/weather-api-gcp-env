import os
import requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, Float, String, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
USERNAME = os.getenv("API_USERNAME")
PASSWORD = os.getenv("API_PASSWORD")

LOCATIONS = [
    ("Limassol", 34.7071, 33.0226),
    ("Paphos", 34.7750, 32.4297),
    ("Nicosia", 35.1856, 33.3823),
]

Base = declarative_base()

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    latitude = Column(Float)
    longitude = Column(Float)
    forecasts = relationship("Forecast", back_populates="location")

class Forecast(Base):
    __tablename__ = "forecasts"
    id = Column(Integer, primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id"))
    date = Column(Date)
    temperature = Column(Float)
    location = relationship("Location", back_populates="forecasts")

engine = create_engine("sqlite:///weather.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

start_date = datetime.utcnow().date()
end_date = start_date + timedelta(days=6)
interval = "PT24H"
parameters = "t_2m:C"

def fetch_forecast(lat, lon):
    url = f"https://api.meteomatics.com/{start_date}T00:00:00Z--{end_date}T00:00:00Z:{interval}/{parameters}/{lat},{lon}/json"
    response = requests.get(url, auth=(USERNAME, PASSWORD))
    response.raise_for_status()
    return response.json()

def store_forecast_data():
    for name, lat, lon in LOCATIONS:
        print(f"Fetching forecast for {name}...")
        data = fetch_forecast(lat, lon)
        location = session.query(Location).filter_by(name=name).first()
        if not location:
            location = Location(name=name, latitude=lat, longitude=lon)
            session.add(location)
            session.commit()
        forecasts = data['data'][0]['coordinates'][0]['dates']
        for entry in forecasts:
            date_val = datetime.fromisoformat(entry["date"].replace("Z", "")).date()
            temp = entry["value"]
            forecast = Forecast(location_id=location.id, date=date_val, temperature=temp)
            session.add(forecast)
    session.commit()
    print("Data stored successfully.")

if __name__ == "__main__":
    store_forecast_data()

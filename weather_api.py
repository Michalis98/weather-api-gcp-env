from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from datetime import date
from typing import List
from weather_fetcher import Base, Location, Forecast

app = FastAPI(title="Weather Forecast API")

engine = create_engine("sqlite:///weather.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.get("/locations")
def get_locations():
    session = SessionLocal()
    try:
        locations = session.query(Location).all()
        return [{"id": loc.id, "name": loc.name, "latitude": loc.latitude, "longitude": loc.longitude} for loc in locations]
    finally:
        session.close()

@app.get("/forecasts/latest")
def get_latest_forecasts():
    session = SessionLocal()
    try:
        results = session.query(Forecast.location_id, Location.name, Forecast.date, func.max(Forecast.id).label("latest_id")).join(Location).group_by(Forecast.location_id, Forecast.date).all()
        latest_forecasts = []
        for loc_id, name, dt, latest_id in results:
            temp = session.query(Forecast.temperature).filter_by(id=latest_id).scalar()
            latest_forecasts.append({"location": name, "date": dt, "temperature": temp})
        return latest_forecasts
    finally:
        session.close()

@app.get("/forecasts/averages")
def get_averages():
    session = SessionLocal()
    try:
        locations = session.query(Location).all()
        results = []
        for loc in locations:
            days = session.query(Forecast.date).filter(Forecast.location_id == loc.id).distinct().all()
            for (dt,) in days:
                last_3 = session.query(Forecast.temperature).filter(Forecast.location_id == loc.id, Forecast.date == dt).order_by(Forecast.id.desc()).limit(3).all()
                if last_3:
                    avg_temp = round(sum(t[0] for t in last_3) / len(last_3), 2)
                    results.append({"location": loc.name, "date": dt, "average_temperature": avg_temp})
        return results
    finally:
        session.close()

@app.get("/top/{metric}")
def get_top(metric: str, n: int = Query(3, gt=0)):
    session = SessionLocal()
    try:
        if metric not in ["temperature"]:
            raise HTTPException(status_code=400, detail="Metric not supported")
        subq = session.query(Forecast.location_id, func.avg(Forecast.temperature).label("avg_temp")).group_by(Forecast.location_id).order_by(desc("avg_temp")).limit(n).subquery()
        joined = session.query(Location.name, subq.c.avg_temp).join(subq, Location.id == subq.c.location_id).all()
        return [{"location": name, f"avg_{metric}": round(temp, 2)} for name, temp in joined]
    finally:
        session.close()

FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["sh", "-c", "python weather_fetcher.py && uvicorn weather_api:app --host 0.0.0.0 --port $PORT"]

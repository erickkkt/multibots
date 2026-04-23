FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir vnstock

COPY . /app/python_engine/

EXPOSE 8000

CMD ["python", "-m", "python_engine.server"]

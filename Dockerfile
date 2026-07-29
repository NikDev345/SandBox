FROM python:3.12.0

WORKDIR /app

COPY requirements1.txt .

RUN pip install -r requirements1.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn","main:fast_app"]
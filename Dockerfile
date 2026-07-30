FROM python:3.12.0

WORKDIR /app

COPY requirements1.txt .

# TODO: RUN pip install -r requirements.txt && \ python -m spacy download en_core_web_sm
RUN pip install -r requirements1.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn","main:fast_app", "--host", "0.0.0.0"]
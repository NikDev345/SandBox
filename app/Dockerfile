FROM python:3.13.0

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements1.txt
# TODO: RUN pip install -r requirements.txt && \ python -m spacy download en_core_web_sm

COPY . .

EXPOSE 8001

CMD ["uvicorn","main:fast_app", "--host", "0.0.0.0"]
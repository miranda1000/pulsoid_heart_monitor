FROM python:3.11-bullseye

WORKDIR /app
COPY . .

RUN python3 -m pip install -r requirements.txt

CMD ["python3", "-m", "pagmon"]

FROM python:3.10

COPY . /server
WORKDIR /server

RUN pip install -r requirements.txt

CMD python app.py

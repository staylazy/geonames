FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python3-pip python-dev build-essential
RUN apt-get install -y gunicorn
COPY . /app
WORKDIR /app 
RUN pip install -r requirements.txt
CMD ["gunicorn", "main:app", "-b", "127.0.0.1:8000"]
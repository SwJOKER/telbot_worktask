FROM python

WORKDIR /home

ENV TELEGRAM_API_TOKEN=""


ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone


COPY requirements.txt ./

RUN pip install -r ./requirements.txt
RUN pip install -U apt-get update && apt-get install sqlite3
COPY *.py ./
COPY createdb.sql ./

ENTRYPOINT ["python", "main.py"]
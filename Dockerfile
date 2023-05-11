FROM python:3.7

WORKDIR /app

RUN mkdir /data && mkdir -p /root/.local/share && ln -s /data /root/.local/share/tts

COPY requirements.txt requirements.txt

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

VOLUME [ "/data" ]

ENTRYPOINT ["python3", "wyoming_tts"]
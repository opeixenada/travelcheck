FROM python:3
ADD . /

COPY conf/config.json /root/.travelcheck.json
COPY requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir -r /usr/src/app/requirements.txt

CMD [ "python", "./travelcheck.py" ]

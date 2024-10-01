FROM python:3.12-alpine

ENV TZ=Asia/Shanghai
ENV APP_DIR=/apple-store-monitor

WORKDIR ${APP_DIR}
COPY requirements.txt ./
RUN python -m pip install -r requirements.txt

ADD src ./src
WORKDIR ${APP_DIR}/src

CMD [ "python", "schedule_check_availability.py"]

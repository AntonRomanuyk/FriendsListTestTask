FROM python:3.13
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt
COPY ./app /app/
RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]
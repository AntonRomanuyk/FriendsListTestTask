FROM python:3.13
ENV PYTHONUNBUFFERED 1
WORKDIR /bot
COPY ./bot/requirements.txt /bot/requirements.txt
RUN pip install -r requirements.txt
COPY ./bot /bot/

CMD ["python", "bot.py"]
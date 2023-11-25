FROM python:3.9-alpine

RUN pip install pipenv

COPY Pipfile Pipfile.lock ./

RUN pipenv install --system --deploy

#COPY .env ./
COPY main.py ./

CMD ["python", "./main.py"]

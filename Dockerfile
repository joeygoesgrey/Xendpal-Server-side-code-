FROM python:3.9-slim

WORKDIR /usr/src/app

# Copy the Pipfile and Pipfile.lock into the working directory
COPY Pipfile Pipfile.lock ./

# Install pipenv and project dependencies
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

# Copy the rest of your application's source code
COPY . .


# RUN apt-get update && apt-get install redis-tools

# COPY celery_health_check.sh /usr/src/app/
RUN chmod +x /usr/src/app/celery_health_check.sh
 
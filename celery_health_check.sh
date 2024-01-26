#!/bin/bash

# Ping the Celery worker
celery -A app.core.celery_config inspect ping -d celery@%h





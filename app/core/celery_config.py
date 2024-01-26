from celery import Celery
 

# Initialize your Celery app here with the broker URL
celery_app = Celery('app.api.file_uploads', broker='redis://redis:6379/0', backend='redis://redis:6379/0')

celery_app.autodiscover_tasks(['app.api.file_uploads'])

celery_app.conf.update({
    'worker_pool': 'gevent',  
})
 


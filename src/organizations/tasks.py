from celery import shared_task

from organizations.models import Organization


@shared_task
def count_widgets():
    return Organization.objects.count()

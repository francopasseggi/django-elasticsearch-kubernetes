from celery import shared_task

from organizations.models import Organization


@shared_task
def count_organizations():
    return Organization.objects.count()

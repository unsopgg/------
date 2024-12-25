from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_status_mail(email):
    message = f'''
    Статус вашей заявки был изменен. 
    http://127.0.0.1:8000/tariff/requests/
    '''

    send_mail(
        'Status updated',
        message,
        'kimyunsopbi@gmail.com',
        [email, ],
        fail_silently=False
    )

@shared_task
def send_request_mail(admin_emails):
    message = '''
    Поступила новая заявка.
    http://127.0.0.1:8000/tariff/requests/admin/
    '''

    send_mail(
        'New Request Notification',
        message,
        'kimyunsopbi@gmail.com',
        admin_emails,
        fail_silently=False
    )

@shared_task
def send_update_request_mail(admin_emails):
    message = '''
    Данная заявка была изменена:
    http://127.0.0.1:8000/tariff/requests/admin/
    '''

    send_mail(
        'Request has been updated',
        message,
        'kimyunsopbi@gmail.com',
        admin_emails,
        fail_silently=False
    )
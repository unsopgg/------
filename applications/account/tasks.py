from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_activation_mail(email, activation_code):
    activation_url = f'http://127.0.0.1:8000/account/activate/{activation_code}/'
    message = f'''
    Йоо броски, отдуши за регистрацию.
    Вот твоя ссылка: {activation_url}, активируй свой аккаунт по ней.
    '''

    send_mail(
        'Activate your account',
        message,
        'kimyunsopbi@gmail.com',
        [email, ],
        fail_silently=False
    )
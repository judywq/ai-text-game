from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.http import HttpResponse


def test_email(request, method, to):
    subject = "It Works!"
    message = "This is the body of the email"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [to]

    if method == 1:
        send_mail(subject, message, from_email, recipient_list)
    else:
        msg = EmailMessage(
            subject,
            message,
            from_email,
            recipient_list,
        )
        msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
    return HttpResponse("Email sent!")

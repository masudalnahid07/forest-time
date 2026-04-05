# adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from django_q.tasks import async_task

class MyAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # এই ফাংশনটি ইমেইল পাঠানোর কাজটিকে Django-Q টাস্কে পাঠিয়ে দেয়
        msg = self.render_mail(template_prefix, email, context)
        async_task('django.core.mail.send_mail', 
                msg.subject, 
                msg.body, 
                msg.from_email, 
                [email])
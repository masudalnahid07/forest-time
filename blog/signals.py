from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
# মডেলগুলো সরাসরি ইম্পোর্ট করা ভালো প্র্যাকটিস
from .models import BlogPost, Subscriber 

@receiver(post_save, sender=BlogPost)
def send_newsletter_on_post(sender, instance, created, **kwargs):
    """
    লজিক: 
    ১. পোস্টটি নতুন হতে হবে (created=True)
    ২. আপনার মডেল অনুযায়ী status এর মান 'published' হতে হবে
    """
    if created and instance.status == 'published':
        # যারা একটিভ সাবস্ক্রাইবার তাদের ইমেইল লিস্ট নেওয়া
        subscribers = Subscriber.objects.filter(is_active=True)
        recipient_list = [sub.email for sub in subscribers]
        
        if recipient_list:
            subject = f"New Story: {instance.title} - Forest Time 🌲"
            
            # টেমপ্লেটে ডাটা পাঠানো
            context = {
                'post': instance,
                'site_url': "http://127.0.0.1:8000" # লাইভ হলে https://floorcrafted.com দিবেন
            }
            
            try:
                # ইমেইল টেমপ্লেট রেন্ডার করা
                html_message = render_to_string('emails/new_post_notification.html', context)
                plain_message = strip_tags(html_message)

                # ইমেইল পাঠানো
                send_mail(
                    subject,
                    plain_message,
                    settings.EMAIL_HOST_USER,
                    recipient_list,
                    html_message=html_message,
                    fail_silently=False,
                )
                print(f"Successfully sent email to {len(recipient_list)} subscribers.")
                
            except Exception as e:
                # কোনো কারণে ইমেইল না গেলে টার্মিনালে এরর দেখাবে
                print(f"Failed to send subscription email: {e}")
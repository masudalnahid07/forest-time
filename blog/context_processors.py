# blog/context_processors.py

from .models import Category
from django.db.models import Count

def global_categories(request): # এই নাম এবং স্পেলিং চেক করুন
    return {
        "categories_list": Category.objects.filter(parent=None).annotate(post_count=Count("posts")),
    }
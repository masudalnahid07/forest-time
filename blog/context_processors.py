# blog/context_processors.py

from .models import Category
from .models import StaticPage
from django.db.models import Count

def global_categories(request): # এই নাম এবং স্পেলিং চেক করুন
    return {
        "categories_list": Category.objects.filter(parent=None).annotate(post_count=Count("posts")),
    }


# for footer legal pages
def footer_pages(request):
    """এটি সব টেমপ্লেটে স্ট্যাটিক পেইজগুলোর ডাটা পাঠাবে"""
    return {
        'all_legal_pages': StaticPage.objects.filter(is_active=True).order_by('order')
    }

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .models import *# নিশ্চিত করুন আপনার পোস্ট মডেলের নাম 'Post' কি না

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import BlogPost, Category  # নিশ্চিত করুন আপনার মডেলে এই নামগুলো আছে

# blog/sitemaps.py
from django.contrib.sitemaps import Sitemap
from .models import BlogPost, Category

class PostSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Category.objects.all()

    def location(self, obj):
        return obj.get_absolute_url()
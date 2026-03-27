from django.contrib.sitemaps import Sitemap
from .models import BlogPost, Category

class PostSitemap(Sitemap):
    changefreq = "weekly"  # গুগল কতদিন পর পর চেক করবে
    priority = 0.9        # এই পেজের গুরুত্ব (০.১ থেকে ১.০)

    def items(self):
        # শুধুমাত্র পাবলিশ করা পোস্টগুলো সাইটম্যাপে যাবে
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        # পোস্টটি সর্বশেষ কবে আপডেট হয়েছে
        return obj.updated_at

class CategorySitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Category.objects.all()
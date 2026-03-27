"""
URL configuration for blogsite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from blog.sitemaps import PostSitemap, CategorySitemap


# ১. handler404 ইম্পোর্ট করার প্রয়োজন নেই, সরাসরি ভেরিয়েবল হিসেবে লিখলেই হয়
# তবে ভিউটি ইম্পোর্ট করে রাখা ভালো অথবা স্ট্রিং হিসেবে পাথ দেওয়া যায়।

sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls')), # আপনার ব্লগের সব ইউআরএল এখানে
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# ২. কাস্টম ৪-০-৪ হ্যান্ডলার সেট করা (অ্যাপের নাম 'blog' হলে)
handler404 = 'blog.views.custom_404_view'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

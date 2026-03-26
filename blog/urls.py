from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import custom_upload_function
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie

urlpatterns = [
    # ১. স্ট্যাটিক এবং স্পেসিফিক পাথ (সবার আগে)
    # হোমপেজ ১ মিনিটের জন্য ক্যাশ
    path("", vary_on_cookie(cache_page(60 * 1)(views.home)), name="home"),
    
    # ১. স্ট্যাটিক পাথ
    path("upload/", custom_upload_function, name="custom_upload_file"),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("search/", views.search, name="search"),
    
    # ফিক্স: authors ফাংশন username আর্গুমেন্ট নেয়
    path("author/<str:username>/", views.authors, name="authors"),
    
    # অথেনটিকেশন
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    
    # ২. ডাইনামিক পাথ (প্রিফিক্স সহ)
    path("category/<slug:slug>/", views.category, name="category"),
    
    # --- ট্যাগ এরর ফিক্স করার জন্য এই লাইনটি যোগ করা হয়েছে ---
    path("tag/<slug:slug>/", views.tag_posts, name="tag"), 
    
    path("toggle-status/<int:pk>/", views.toggle_status, name="toggle_status"),
    path('article/edit/<slug:slug>/', views.edit_article, name='edit_article'),
    path('404/', views.custom_404_view, name='error_404'),
    path('live-seo-checker/', views.live_seo_checker, name='live_seo_checker'),

    # ফিক্স: views.tag এর বদলে tag_posts এবং name="tag" (টেমপ্লেটের সাথে মিল রেখে)
    path("tag/<slug:slug>/", views.tag_posts, name="tag"),

    # ৩. ক্যাচ-অল ডাইনামিক পাথ (সবার শেষে থাকবে)
    path("<slug:slug>/", views.single_post, name="single_post"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
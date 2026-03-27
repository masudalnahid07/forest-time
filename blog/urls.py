from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import custom_upload_function

urlpatterns = [
    path("", views.home, name="home"),
    
    # ১. স্ট্যাটিক পাথ
    path("upload/", custom_upload_function, name="custom_upload_file"),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("search/", views.search, name="search"),
    
    # ২. ইউজার প্রোফাইল ও এডিট (অবশ্যই single_post এর উপরে থাকতে হবে)
    path("profile/", views.user_profile, name="profile"), # এই লাইনটি মিসিং ছিল
    path('profile/edit/<str:field_name>/', views.edit_field, name='edit_field'),
    
    # ৩. অথেনটিকেশন (ডুপ্লিকেট রিমুভ করা হয়েছে)
    path("register/", views.register, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page='home'), name="logout"),
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),
    
    # ৪. ডাইনামিক পাথ ও অন্যান্য
    path("author/<str:username>/", views.authors, name="authors"),
    path("category/<slug:slug>/", views.category, name="category"),
    path("toggle-status/<int:pk>/", views.toggle_status, name="toggle_status"),
    path('article/edit/<slug:slug>/', views.edit_article, name='edit_article'),
    path('404/', views.custom_404_view, name='error_404'),
    path('live-seo-checker/', views.live_seo_checker, name='live_seo_checker'),
    path("tag/<slug:slug>/", views.tag_posts, name="tag"),
    path("reply/<int:comment_id>/", views.post_reply, name="post_reply"),

    # ৫. ক্যাচ-অল ডাইনামিক পাথ (সবার শেষে থাকবে)
    path("<slug:slug>/", views.single_post, name="single_post"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
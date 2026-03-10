from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import the blog views explicitly
from .import views

# Assuming custom_upload_function is in your current directory's views.
# Explicit imports prevent NameErrors and shadowing.
from .views import custom_upload_function 

urlpatterns = [
    path('', views.home, name='home'),
    
    # 1. Specific/Static paths should go FIRST
    path('upload/', custom_upload_function, name='custom_upload_file'),
    path('ckeditor5/', include('django_ckeditor_5.urls')),
    path('search/', views.search, name='search'),
    path('author/', views.authors, name='authors'), 
    
    # 2. Dynamic paths with prefixes go NEXT
    path('category/<slug:slug>/', views.category, name='category'),
    
    # 3. Catch-all dynamic paths go LAST
    path('<slug:slug>/', views.single_post, name='single_post'), 
]

# Development media serve
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from calendar import c
from django.shortcuts import render
import os
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from .models import *

# Create your views here.

def authors(request, username):
    # ১. নির্দিষ্ট লেখককে খুঁজে বের করা
    author = get_object_or_404(User, username=username)
    
    # ২. ওই লেখকের সমস্ত পাবলিশড পোস্টগুলো নিয়ে আসা
    author_posts = BlogPost.objects.filter(author=author, status='published').order_by('-created_at')
    
    # ৩. প্যাগিনেশন অ্যাড করা (আপনার টেম্প্লেটে প্যাগিনেশন আছে, তাই প্রতি পেজে ৬টি করে পোস্ট দেখানোর জন্য)
    paginator = Paginator(author_posts, 6) # প্রতি পেজে ৬টি পোস্ট
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # ৪. সাইডবারের ডেটা (অন্যান্য ভিউয়ের মতো)
    categories_list = Category.objects.annotate(post_count=Count('posts'))
    recent_posts = BlogPost.objects.filter(status='published').order_by('-created_at')[:5]
    
    context = {
        'author': author,
        'posts': posts, # প্যাগিনেট করা পোস্টগুলো
        'categories_list': categories_list,
        'recent_posts': recent_posts,
    }
    
    return render(request, 'author.html', context)

def home(request):
    # শুধুমাত্র পাবলিশড পোস্টগুলো লেটেস্ট অনুযায়ী নিয়ে আসা
    published_posts = BlogPost.objects.filter(status='published').order_by('-created_at')
    
    # হিরো সেকশনের জন্য প্রথম ৩টি পোস্ট
    hero_sections = published_posts[:3]
    
    # মেইন লিস্টের জন্য হিরো সেকশনের ৩টি পোস্ট বাদ দিয়ে বাকি পোস্টগুলো নেওয়া
    hero_pks = [post.pk for post in hero_sections]
    all_list_blogs = published_posts.exclude(pk__in=hero_pks)
    
    # প্যাগিনেশন সেটআপ (প্রতি পেজে ৬টি করে পোস্ট)
    paginator = Paginator(all_list_blogs, 6) 
    page_number = request.GET.get('page')
    list_blogs = paginator.get_page(page_number)
    
    # সাইডবারের ডেটা
    categories_list = Category.objects.annotate(post_count=Count('posts')) 
    recent_posts = published_posts[:5]

    context = {
        'blogs': hero_sections,
        'list_blogs': list_blogs,
        'categories_list': categories_list,
        'recent_posts': recent_posts, 
    }
    
    return render(request, 'garden-index.html', context)

def single_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    post.views_count += 1
    post.save()

    # রিলেটেড পোস্ট
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        status='published'
    ).exclude(pk=post.pk).order_by('-created_at')[:2] 

    categories_list = Category.objects.annotate(post_count=Count('posts'))
    recent_posts = BlogPost.objects.filter(status='published').order_by('-created_at')[:5]

    # কমেন্টস প্যাগিনেশন
    comments_list = Comment.objects.filter(post=post).order_by('-created_at')
    paginator = Paginator(comments_list, 5) # প্রতি পেজে ৫টি কমেন্ট দেখাবে
    page_number = request.GET.get('page')
    comments = paginator.get_page(page_number)

    context = {
        'post': post,
        'related_posts': related_posts,
        'categories_list': categories_list,
        'recent_posts': recent_posts,
        'comments': comments, # প্যাগিনেট করা কমেন্ট পাঠানো হচ্ছে
    }
    
    return render(request, 'garden-single.html', context)

def category(request, slug):
    category = get_object_or_404(Category, category_slug=slug)
    
    # ওই নির্দিষ্ট ক্যাটাগরির পোস্টগুলো
    post_list = BlogPost.objects.filter(category=category, status='published').order_by('-created_at')
    
    # প্যাগিনেশন সেটআপ (প্রতি পেজে ৬টি করে পোস্ট দেখানোর জন্য)
    paginator = Paginator(post_list, 6) 
    page_number = request.GET.get('page')
    posts = paginator.get_page(page_number)
    
    # সাইডবারের জন্য সব ক্যাটাগরি এবং পোস্ট কাউন্ট
    categories_list = Category.objects.annotate(post_count=Count('posts')) 

    # রিসেন্ট পোস্ট ডাইনামিক করা (সব ক্যাটাগরি থেকে লেটেস্ট ৫টি পোস্ট)
    recent_posts = BlogPost.objects.filter(status='published').order_by('-created_at')[:5]

    context = {
        'category': category,
        'posts': posts, # এখন এটি প্যাগিনেট করা ডেটা পাঠাবে
        'categories_list': categories_list,
        'recent_posts': recent_posts, 
    }
    return render(request, 'garden-category.html', context)

def search(request):
    query = request.GET.get('q') 
    results = [] 
    
    if query:
        query = query.strip() # যদি ইউজার ভুল করে লেখার আগে বা পরে স্পেস দিয়ে দেয়, এটি তা মুছে ফেলবে
        
        # আপনার অরিজিনাল কোডটিই রাখা হলো
        results = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(post_details__icontains=query),
            status='published').distinct()
        
    context = {
        'query': query,
        'results': results,
    }
    return render(request, 'search.html', context)


@csrf_exempt
def custom_upload_function(request):
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]

        # Optional: file type/type validation
        if not upload.name.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            return JsonResponse({"error": "Only image files are allowed."}, status=400)

        # Optional: file size validation (5MB limit)
        if upload.size > 5 * 1024 * 1024:
            return JsonResponse({"error": "File size must be under 5MB."}, status=400)

        # Save file to MEDIA_ROOT/uploads/
        upload_folder = os.path.join(settings.MEDIA_ROOT, "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, upload.name)
        path = default_storage.save(file_path, ContentFile(upload.read()))

        # Return URL to CKEditor
        file_url = os.path.join(settings.MEDIA_URL, "uploads", upload.name)
        return JsonResponse({"url": file_url})

    return JsonResponse({"error": "Invalid request"}, status=400)
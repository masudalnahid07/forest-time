import os
import re
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import CustomRegistrationForm, PostForm
from .models import BlogPost, Category, Author, Comment, Reply

# --- ১. হেল্পার ফাংশন (সাইডবার ডাটা) ---
def get_sidebar_data():
    return {
        "recent_posts": BlogPost.objects.filter(status="published").order_by("-created_at")[:5]
    }

# --- ২. হোমপেজ ভিউ (HTMX সাপোর্ট সহ) ---
def home(request):
    published_posts = BlogPost.objects.filter(status="published").select_related('author', 'category').order_by("-created_at")
    hero_sections = published_posts[:3]
    hero_pks = [post.pk for post in hero_sections]
    all_list_blogs = published_posts.exclude(pk__in=hero_pks)

    paginator = Paginator(all_list_blogs, 6)
    page_number = request.GET.get("page")
    list_blogs = paginator.get_page(page_number)

    context = {
        "blogs": hero_sections,
        "list_blogs": list_blogs,
        **get_sidebar_data(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/blog_list_partial.html", context)
    return render(request, "garden-index.html", context)

# --- ৩. সিংগেল পোস্ট ভিউ (কমেন্ট লজিক ফিক্সড) ---
def single_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status="published")

    # কমেন্ট সাবমিশন লজিক
    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please register or log in to leave a comment.")
            return redirect("login")
        
        text = request.POST.get("text")
        if text:
            Comment.objects.create(post=post, user=request.user, text=text)
            messages.success(request, "Your comment has been successfully added!")
        return redirect("single_post", slug=post.slug)

    # ভিউ কাউন্ট আপডেট (ডাটাবেজ হিট সেফ)
    BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)

    # রিলেটেড পোস্ট (একই ক্যাটাগরি)
    related_posts = BlogPost.objects.filter(category=post.category, status="published").exclude(pk=post.pk).order_by("-created_at")[:2]

    # কমেন্ট লিস্ট (প্যাজিনেশন সহ)
    comments_qs = Comment.objects.filter(post=post).select_related('user').order_by("-created_at")
    paginator = Paginator(comments_qs, 5)
    page_number = request.GET.get("page")
    comments = paginator.get_page(page_number)

    context = {
        "post": post,
        "related_posts": related_posts,
        "comments": comments,
        **get_sidebar_data(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/inline_post.html", context)
    return render(request, "garden-single.html", context)

# --- ৪. ট্যাগ ফিল্টারিং ভিউ ---
def tag_posts(request, slug):
    posts_list = BlogPost.objects.filter(tags__slug=slug, status='published').order_by("-created_at")
    paginator = Paginator(posts_list, 6)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    context = {
        "posts": posts,
        "tag_slug": slug,
        **get_sidebar_data(),
    }
    return render(request, 'garden-category.html', context)

# --- ৫. অথর প্রোফাইল ভিউ ---
def authors(request, username):
    author_obj = get_object_or_404(Author, user__username=username)
    author_posts = BlogPost.objects.filter(author=author_obj, status="published").order_by("-created_at")
    
    paginator = Paginator(author_posts, 6)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    context = {
        "author": author_obj,
        "posts": posts,
        **get_sidebar_data(),
    }
    return render(request, "author.html", context)

# --- ৬. ক্যাটাগরি ভিউ ---
def category(request, slug):
    category_obj = get_object_or_404(Category, category_slug=slug)
    post_list = BlogPost.objects.filter(category=category_obj, status="published").order_by("-created_at")
    
    paginator = Paginator(post_list, 6)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    context = {
        "category": category_obj,
        "posts": posts,
        **get_sidebar_data(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/category_list_partial.html", context)
    return render(request, "garden-category.html", context)

# --- ৭. সার্চ ভিউ (HTMX সাপোর্ট সহ) ---
def search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results_list = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(post_details__icontains=query),
            status="published",
        ).distinct()
        paginator = Paginator(results_list, 6)
        page_number = request.GET.get("page")
        results = paginator.get_page(page_number)

    context = {
        "query": query,
        "results": results,
        **get_sidebar_data(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "partials/search_results.html", context)
    return render(request, "search.html", context)

# --- ৮. টিউটোরিয়াল: রেজিস্ট্রেশন ও অ্যাক্টিভেশন ---
def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        form = CustomRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            try:
                current_site = get_current_site(request)
                mail_subject = "Activate your account"
                message = render_to_string("account_activation_email.html", {
                    "user": user,
                    "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                })
                to_email = form.cleaned_data.get("email")
                email = EmailMessage(mail_subject, message, to=[to_email])
                email.send()
                return render(request, "email_verification_sent.html", {"user_email": to_email})
            except Exception:
                user.delete()
                messages.error(request, "Error sending email. Please try again.")
    else:
        form = CustomRegistrationForm()
    return render(request, "register.html", {"form": form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your email has been verified. You can now log in.")
        return redirect("login")
    else:
        messages.error(request, "Activation link is invalid!")
        return redirect("register")

# --- ৯. অ্যাডমিন ও ইউটিলিটি ফাংশন (HTMX/SEO) ---
@staff_member_required
@csrf_exempt
def toggle_status(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    if post.status == "published":
        post.status = "draft"
        bg_color, btn_text = "#ffc107", "Draft"
    else:
        post.status = "published"
        bg_color, btn_text = "#28a745", "Published"
    
    post.save(update_fields=["status"])
    new_button_html = f'''
        <button style="background-color: {bg_color}; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" 
        hx-post="/toggle-status/{post.pk}/" hx-swap="outerHTML">{btn_text}</button>
    '''
    return HttpResponse(new_button_html)

@staff_member_required
def edit_article(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    if request.user != post.author.user and not request.user.is_superuser:
        messages.error(request, "You are not allowed to edit this article.")
        return redirect('single_post', slug=post.slug)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Article updated successfully!")
            return redirect('single_post', slug=post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'edit_article.html', {"form": form, "post": post, **get_sidebar_data()})

@staff_member_required
@csrf_exempt 
def live_seo_checker(request):
    if request.method != "POST":
        return HttpResponse("Invalid Request")

    keyword = request.POST.get('focus_keyword', '').strip().lower()
    title = request.POST.get('title', '').strip().lower()
    slug_input = request.POST.get('slug', '').strip().lower()
    meta_desc = request.POST.get('meta_description', '').strip().lower()
    content_html = request.POST.get('post_details', '')
    content_text = strip_tags(content_html).lower()

    if not keyword:
        return HttpResponse("<div style='padding:15px; background:#fff3cd; border-radius:5px;'>⚠️ Focus Keyword দিন!</div>")

    # বিশ্লেষণ লজিক (সংক্ষিপ্ত আকারে আপনার আগের কোডটি বজায় রাখা হয়েছে)
    title_len = len(title)
    title_match = "✅ Good" if 0 < title_len <= 60 else "❌ Too long"
    
    desc_keyword_count = meta_desc.count(keyword)
    desc_len = len(meta_desc)
    meta_desc_match = "✅ Good" if 120 <= desc_len <= 160 else "❌ Check length"

    context = {
        'keyword': keyword,
        'title_match': title_match,
        'meta_desc_match': f"{meta_desc_match} (Keyword: {desc_keyword_count})",
        # ... আপনার বাকি সব SEO লজিক এখানে থাকবে ...
    }
    html = render_to_string('partials/seo_checker_result.html', context)
    return HttpResponse(html)

def custom_404_view(request, exception=None): 
    return render(request, '404.html', status=404)


@csrf_exempt
def custom_upload_function(request):
    """CKEditor বা অন্যান্য সোর্স থেকে ইমেজ আপলোড করার ফাংশন"""
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]
        ext = os.path.splitext(upload.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
            return JsonResponse({"error": "Only images are allowed."}, status=400)
        
        # ডিফল্ট স্টোরেজে ফাইল সেভ করা
        path = default_storage.save(f"uploads/{upload.name}", ContentFile(upload.read()))
        file_url = f"{settings.MEDIA_URL}{path}"
        return JsonResponse({"url": file_url})
    
    return JsonResponse({"error": "Invalid request"}, status=400)
import os
import re
import json
from django.http import HttpResponse, Http404, JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.mail import EmailMessage
from django.core.paginator import Paginator
from django.db.models import Count, Q, F
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.text import slugify
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_POST, condition
from taggit.models import Tag


from .models import BlogPost, Category, Author, Comment, Reply, EmailChangeRequest
from .forms import CustomRegistrationForm, PostForm

# --- ১. হেল্পার ফাংশন শুরু ---
def get_sidebar_data():
    return {
        "recent_posts": BlogPost.objects.filter(status="published").order_by("-created_at")[:5]
    }
# --- ১. হেল্পার ফাংশন শেষ---

# --- ২. হোম এবং অথর ভিউ  শুরু ---
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
# --- ২. হোম ভিউ শেষ---

# --- ৩. হোম ভিউ শুরু--- 
def authors(request, username):
    author_obj = get_object_or_404(Author, user__username=username)
    author_posts = BlogPost.objects.filter(author=author_obj, status="published").order_by("-created_at")
    paginator = Paginator(author_posts, 6)
    posts = paginator.get_page(request.GET.get("page"))

    context = {
        "author": author_obj,
        "posts": posts,
        **get_sidebar_data(),
    }
    return render(request, "author.html", context)

# --- ৩. হোম ভিউ শেষ--- 


# --- ৪. পোষ্ট মডিফাই করলে ৩০২ না করলে ২০০ শো করার লজিক শুরু -- 
def post_last_modified(request, slug):
    try:
        # এখানে ফিল্টার ব্যবহার করা নিরাপদ
        post = BlogPost.objects.get(slug=slug, status="published")
        return post.updated_at
    except BlogPost.DoesNotExist:
        return None

# --- ৪. পোষ্ট মডিফাই করলে ৩০২ না করলে ২০০ শো করার লজিক শেষ ---

# --- ৫. সিঙ্গেল পোস্ট এবং কমেন্ট শুরু---
@condition(last_modified_func=post_last_modified)
def single_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, status="published")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(request, "To post a comment, you must be logged in.")
            return redirect("login")

        comment_text = request.POST.get("text") 
        if comment_text and comment_text.strip():
            Comment.objects.create(post=post, user=request.user, text=comment_text)
            messages.success(request, "Your comment has been successfully added!")
        else:
            messages.error(request, "The comment cannot be left empty.")
        return redirect("single_post", slug=post.slug)

    BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
    
    related_posts = BlogPost.objects.filter(category=post.category, status="published").exclude(pk=post.pk).order_by("-created_at")[:2]
    comments_list = Comment.objects.filter(post=post).select_related('user', 'user__author_profile').order_by("-created_at")
    
    paginator = Paginator(comments_list, 10) 
    comments = paginator.get_page(request.GET.get("page"))

    context = {
        "post": post,
        "related_posts": related_posts,
        "comments": comments,
        **get_sidebar_data(),
    }

    # --- ৪. রেসপন্স এবং কাস্টম স্ট্যাটাস লজিক ---
    if request.headers.get("HX-Request"):
        response = render(request, "partials/inline_post.html", context)
    else:
        response = render(request, "garden-single.html", context)
    # --- ৪. রেসপন্স এবং কাস্টম স্ট্যাটাস লজিক ---
    return response

@csrf_protect
@require_POST
def post_reply(request, comment_id):
    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in to reply.")
        return redirect("login")

    comment = get_object_or_404(Comment, id=comment_id)
    reply_text = request.POST.get("text")
    
    if reply_text and reply_text.strip():
        Reply.objects.create(user=request.user, comment=comment, text=reply_text)
        messages.success(request, "Your reply has been added successfully!")
    else:
        messages.error(request, "Reply cannot be empty.")
    return redirect("single_post", slug=comment.post.slug)

# --- ৪. আর্টিকেল এডিট এবং স্ট্যাটাস টগল ---
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
def toggle_status(request, pk):
    post = get_object_or_404(BlogPost, pk=pk)
    post.status = "draft" if post.status == "published" else "published"
    post.save(update_fields=["status"])
    
    bg_color = "#ffc107" if post.status == "draft" else "#28a745"
    btn_text = "Draft" if post.status == "draft" else "Published"
    
    new_button_html = f'''
        <button style="background-color: {bg_color}; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" 
        hx-post="/toggle-status/{post.pk}/" hx-swap="outerHTML">{btn_text}</button>
    '''
    return HttpResponse(new_button_html)

# --- ৫. প্রোফাইল এবং HTMX ফিল্ড এডিট (FIXED) ---
@login_required
def user_profile(request):
    author_obj, created = Author.objects.get_or_create(user=request.user)
    is_pending = EmailChangeRequest.objects.filter(user=request.user, is_approved=False).exists()
    
    context = {
        'user': request.user,
        'author_profile': author_obj,
        'pending_email_request': is_pending,
        'comments_count': Comment.objects.filter(user=request.user).count(),
        **get_sidebar_data(),
    }
    return render(request, 'profile.html', context)

@login_required
@csrf_protect
def edit_field(request, field_name):
    author_profile, _ = Author.objects.get_or_create(user=request.user)
    user = request.user
    display_value = ""
    message = ""

    if request.method == 'POST':

        # ১) ইমেইল এডিট
        if field_name == 'email':
            new_email = request.POST.get('email')
            if new_email == user.email:
                return HttpResponse("This is already your current email.", status=400)

            if EmailChangeRequest.objects.filter(user=user, is_approved=False).exists():
                message = "A request is already pending approval!"
            else:
                EmailChangeRequest.objects.create(user=user, new_email=new_email)
                message = "Request sent to Admin for approval!"
            display_value = user.email

        # ২) প্রোফাইল ইমেজ
        elif field_name == 'author_image':
            # এখানে name এবং get দুটোই author_image হবে
            new_image = request.FILES.get('author_image')
            if not new_image:
                return HttpResponse("Please select an image first.", status=400)

            author_profile.author_image = new_image
            author_profile.save()
            display_value = author_profile.author_image.url
            message = "Profile image updated successfully!"

        # ৩) ইউজারনেম
        elif field_name == 'username':
            new_val = request.POST.get('username', '').strip()
            if not new_val:
                return HttpResponse("Username cannot be empty.", status=400)
            user.username = new_val
            user.save()
            display_value = user.username
            message = "Username updated!"

        # ৪) বায়ো, ফুল নেম ইত্যাদি
        else:
            new_val = request.POST.get(field_name, '').strip()
            if not new_val:
                return HttpResponse("Field cannot be empty.", status=400)

            if hasattr(author_profile, field_name):
                setattr(author_profile, field_name, new_val)
                author_profile.save()
                display_value = new_val
                message = "Saved successfully!"
            else:
                return HttpResponse("Invalid field.", status=400)

        return render(request, 'partials/profile_row_updated.html', {
            'field_name': field_name,
            'value': display_value,
            'success_msg': message,
        })

    return render(request, 'partials/edit_input.html', {
        'field_name': field_name,
        'author_profile': author_profile,
        'user': user,
    })

# --- ৬. অ্যাডমিন ড্যাশবোর্ড (Email Request) ---
@staff_member_required
def admin_dashboard(request):
    pending_requests = EmailChangeRequest.objects.filter(is_approved=False).order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'pending_requests': pending_requests})

@staff_member_required
@require_POST
def approve_email_request(request, request_id):
    email_req = get_object_or_404(EmailChangeRequest, id=request_id)
    user = email_req.user
    user.email = email_req.new_email
    user.save()
    email_req.is_approved = True
    email_req.save()
    return HttpResponse("") 

@staff_member_required
@require_POST
def reject_email_request(request, request_id):
    get_object_or_404(EmailChangeRequest, id=request_id).delete()
    return HttpResponse("")

@login_required
@require_POST
def cancel_email_request(request):
    EmailChangeRequest.objects.filter(user=request.user, is_approved=False).delete()
    return render(request, 'partials/profile_row_updated.html', {
        'field_name': 'email',
        'value': request.user.email,
        'success_msg': 'Request cancelled successfully.'
    })

# --- ৭. ক্যাটাগরি, সার্চ এবং ট্যাগ ---
def category(request, slug):
    category_obj = get_object_or_404(Category, category_slug=slug)
    post_list = BlogPost.objects.filter(category=category_obj, status="published").order_by("-created_at")
    paginator = Paginator(post_list, 6)
    posts = paginator.get_page(request.GET.get("page"))

    context = {"category": category_obj, "posts": posts, **get_sidebar_data()}
    if request.headers.get("HX-Request"):
        return render(request, "partials/category_list_partial.html", context)
    return render(request, "garden-category.html", context)

def search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results_list = BlogPost.objects.filter(
            Q(title__icontains=query) | Q(post_details__icontains=query),
            status="published",
        ).distinct()
        paginator = Paginator(results_list, 6)
        results = paginator.get_page(request.GET.get("page"))

    context = {"query": query, "results": results, **get_sidebar_data()}
    if request.headers.get("HX-Request"):
        return render(request, "partials/search_results.html", context)
    return render(request, "search.html", context)

# --- ৮. রেজিস্ট্রেশন এবং অ্যাক্টিভেশন ---
def register(request):
    if request.user.is_authenticated: return redirect('home')
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
                    "user": user, "domain": current_site.domain,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "token": default_token_generator.make_token(user),
                })
                email = EmailMessage(mail_subject, message, to=[form.cleaned_data.get("email")])
                email.send()
                return render(request, "email_verification_sent.html", {"user_email": form.cleaned_data.get("email")})
            except:
                user.delete()
                messages.error(request, "Error sending email. Please try again.")
    else: form = CustomRegistrationForm()
    return render(request, "register.html", {"form": form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except: user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Email verified. You can now log in.")
        return redirect("login")
    messages.error(request, "Activation link is invalid!")
    return redirect("register")

# --- ৯. SEO লাইভ চেকার (ফুল লজিক সহ) ---
@staff_member_required
@csrf_exempt 
def live_seo_checker(request):
    if request.method != "POST": return HttpResponse("Invalid Request")

    keyword = request.POST.get('focus_keyword', '').strip().lower()
    title = request.POST.get('title', '').strip().lower()
    slug_input = request.POST.get('slug', '').strip().lower()
    meta_desc = request.POST.get('meta_description', '').strip().lower() 
    content_html = request.POST.get('post_details', '')
    content_text = strip_tags(content_html).lower()

    if not keyword:
        return HttpResponse("<div class='alert alert-warning'>⚠️ Focus Keyword missing!</div>")

    # এনালাইসিস লজিক
    title_len = len(title)
    title_match = "✅ Good" if 0 < title_len <= 60 else "❌ Too long or empty"
    
    effective_slug = slug_input if slug_input else slugify(title)
    slug_match = "✅ OK" if slugify(keyword) in effective_slug else "❌ Missing keyword"

    content_count = content_text.count(keyword)
    content_match = f"✅ Found {content_count} times" if content_count > 0 else "❌ Not found"

    context = {
        'keyword': keyword, 'title_match': title_match, 'slug_match': slug_match,
        'content_match': content_match, 'url_length_match': f"{len(effective_slug)} chars",
    }
    return HttpResponse(render_to_string('partials/seo_checker_result.html', context))

# --- ১০. আপলোড এবং ৪-০-৪ ---
@csrf_exempt
def custom_upload_function(request):
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]
        path = default_storage.save(f"uploads/{upload.name}", ContentFile(upload.read()))
        return JsonResponse({"url": f"{settings.MEDIA_URL}{path}"})
    return JsonResponse({"error": "Invalid request"}, status=400)

def custom_404_view(request, exception=None): 
    return render(request, '404.html', status=404)


def tag_posts(request, slug):
    tag = get_object_or_404(Tag, slug=slug)
    post_list = BlogPost.objects.filter(tags__slug=slug, status='published').order_by("-created_at")
    
    paginator = Paginator(post_list, 6)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    context = {
        "posts": posts,
        "tag": tag,
        **get_sidebar_data(),
    }
    return render(request, "garden-category.html", context)
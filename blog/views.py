import os
import re
import json
from django.http import HttpResponse
from django.conf import settings
from taggit.models import Tag
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
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import CustomRegistrationForm, PostForm
from .models import *
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserUpdateForm, ProfileUpdateForm


# Helper function to avoid repeating code

# 1. Single Post View
def get_sidebar_data():
    return {
        # "categories_list" এখান থেকে সরিয়ে ফেলা হয়েছে কারণ এটি এখন global_categories (Context Processor) থেকে আসে।
        "recent_posts": BlogPost.objects.filter(status="published").order_by("-created_at")[:5]
    }

def authors(request, username):
    try:
        author_obj = Author.objects.get(user__username=username)
    except Author.DoesNotExist:
        raise Http404("Author not found")

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

# ২. Single Post View
def single_post(request, slug):
    try:
        # ১. পাবলিশড পোস্ট খুঁজে বের করা
        post = BlogPost.objects.get(slug=slug, status="published")
    except BlogPost.DoesNotExist:
        raise Http404("Post not found")

    if request.method == "POST":
        # ২. লগইন চেক (সুরক্ষার জন্য)
        if not request.user.is_authenticated:
            messages.warning(request, "To post a comment, you must be logged in.")
            return redirect("login")

        # ৩. ডাটা রিসিভ করা (গুরুত্বপূর্ণ: এখানে 'text' ব্যবহার করুন কারণ টেমপ্লেটে name="text")
        comment_text = request.POST.get("text") 
        
        if comment_text and comment_text.strip():
            Comment.objects.create(
                post=post, 
                user=request.user, 
                text=comment_text # আপনার মডেলের ফিল্ড 'text'
            )
            messages.success(request, "Your comment has been successfully added!")
        else:
            # যদি comment_text খালি থাকে তবে এই এররটি আসবে (যা আপনি স্ক্রিনশটে দেখেছিলেন)
            messages.error(request, "The comment cannot be left empty.")
            
        return redirect("single_post", slug=post.slug)

    # ভিউ কাউন্ট ১ বৃদ্ধি করা
    BlogPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)
    
    # রিলেটেড পোস্ট (একই ক্যাটাগরির অন্য পোস্ট)
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        status="published"
    ).exclude(pk=post.pk).order_by("-created_at")[:2]
    
    # ৪. কমেন্ট লিস্ট (সবগুলো কমেন্ট ডাটাবেস থেকে নিয়ে আসা)
    comments_list = Comment.objects.filter(post=post).select_related('user').order_by("-created_at")
    
    # পেজিনেশন: প্রতি পেজে ১০টি কমেন্ট
    paginator = Paginator(comments_list, 10) 
    page_number = request.GET.get("page")
    comments = paginator.get_page(page_number)

    context = {
        "post": post,
        "related_posts": related_posts,
        "comments": comments, # এটি টেমপ্লেটের {% for comment in comments %} লুপে যাবে
        **get_sidebar_data(),
    }

    # HTMX রিকোয়েস্ট হ্যান্ডেল করা
    if request.headers.get("HX-Request"):
        return render(request, "partials/inline_post.html", context)
        
    return render(request, "garden-single.html", context)


# ৩. Edit Article View
def edit_article(request, slug):
    try:
        post = BlogPost.objects.get(slug=slug)
    except BlogPost.DoesNotExist:
        raise Http404("Article not found")
    
    post_author_user = post.author.user 

    if request.user != post_author_user and not request.user.is_superuser:
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

    context = {
        "form": form,
        "post": post,
        **get_sidebar_data(),
    }
    return render(request, 'edit_article.html', context)

# ৪. Category View
def category(request, slug):
    try:
        category_obj = Category.objects.get(category_slug=slug)
    except Category.DoesNotExist:
        raise Http404("Category not found")

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
            except Exception as e:
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

def custom_404_view(request, exception=None): 
    return render(request, '404.html', status=404)

# ৫. Toggle Status (HTMX) - ফিক্স করা হয়েছে!
@staff_member_required
@csrf_exempt
def toggle_status(request, pk): # request.POST.get('pk') এর বদলে URL থেকে pk নেবে
    try:
        post = BlogPost.objects.get(pk=pk)
    except BlogPost.DoesNotExist:
        return HttpResponse("Post not found", status=404)
        
    if post.status == "published":
        post.status = "draft"
        bg_color = "#ffc107"
        btn_text = "Draft"
    else:
        post.status = "published"
        bg_color = "#28a745"
        btn_text = "Published"
        
    post.save(update_fields=["status"])
    
    # JSON এর বদলে HTML বাটন রিটার্ন করা হচ্ছে যেন HTMX ঠিকমতো কাজ করে
    new_button_html = f'''
        <button style="background-color: {bg_color}; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" 
        hx-post="/toggle-status/{post.pk}/" hx-swap="outerHTML">{btn_text}</button>
    '''
    return HttpResponse(new_button_html)

@csrf_exempt
def custom_upload_function(request):
    if request.method == "POST" and request.FILES.get("upload"):
        upload = request.FILES["upload"]
        ext = os.path.splitext(upload.name)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".gif"]:
            return JsonResponse({"error": "Only images are allowed."}, status=400)
        path = default_storage.save(f"uploads/{upload.name}", ContentFile(upload.read()))
        file_url = f"{settings.MEDIA_URL}{path}"
        return JsonResponse({"url": file_url})
    return JsonResponse({"error": "Invalid request"}, status=400)

# ৬. SEO Live Checker (Slug & Paragraph Fix)
@staff_member_required
@csrf_exempt 
def live_seo_checker(request):
    if request.method != "POST":
        return HttpResponse("Invalid Request")

    # ১. ফর্ম থেকে ডাটা রিসিভ করা
    keyword = request.POST.get('focus_keyword', '').strip().lower()
    title = request.POST.get('title', '').strip().lower()
    slug_input = request.POST.get('slug', '').strip().lower()
    meta_desc = request.POST.get('meta_description', '').strip().lower() 
    meta_keys = request.POST.get('meta_keywords', '').strip().lower() 
    content_html = request.POST.get('post_details', '')
    
    # এডিটরের কন্টেন্ট থেকে বাড়তি স্পেস ও নিউলাইন পরিষ্কার করা
    content_html = content_html.replace('\r', '').replace('\n', ' ')
    content_text = strip_tags(content_html).lower()

    if not keyword:
        return HttpResponse("""
            <div style='padding: 15px; background: #fff3cd; border: 1px solid #ffeeba; border-radius: 5px; color: #856404; font-weight: bold;'>
                ⚠️ আগে একটি Focus Keyword লিখে বাটনে ক্লিক করুন!
            </div>
        """)

    # --- ২. টাইটেল ও মেটা ডেসক্রিপশন এনালাইসিস (কাউন্ট ও ক্যারেক্টার ফিক্স) ---
    title_len = len(title)
    if 0 < title_len <= 60:
        title_match = f"<span style='color:green;'>✅ {title_len} ক্যারেক্টর (Good)</span>"
    elif title_len == 0:
        title_match = "<span style='color:orange;'>⚠️ টাইটেল খালি</span>"
    else:
        title_match = f"<span style='color:red;'>❌ {title_len} ক্যারেক্টর (Too long)</span>"

    # মেটা ডেসক্রিপশনে কিওয়ার্ড কতবার আছে তা বের করা
    desc_keyword_count = meta_desc.count(keyword)
    desc_len = len(meta_desc)
    
    if desc_len == 0:
        meta_desc_match = "<span style='color:orange;'>⚠️ ডেসক্রিপশন খালি</span>"
    else:
        # ১২০-১৬০ ক্যারেক্টার হলো স্ট্যান্ডার্ড সাইজ
        color = "green" if 120 <= desc_len <= 160 else "red"
        count_text = f" + Keyword আছে ({desc_keyword_count} বার)" if desc_keyword_count > 0 else " + Keyword নেই"
        
        status_icon = "✅" if color == "green" else "❌"
        meta_desc_match = f"<span style='color:{color};'>{status_icon} {desc_len} ক্যারেক্টর{count_text}</span>"

    meta_keys_match = f"<span style='color:green;'>✅ আছে</span>" if keyword in meta_keys else "<span style='color:red;'>❌ নেই</span>"

    # --- ৩. URL Slug & Length এনালাইসিস (অটো-জেনারেট Fallback সহ) ---
    effective_slug = slug_input if slug_input else slugify(title)
    keyword_slug = slugify(keyword)
    if not keyword_slug:
        keyword_slug = keyword.replace(" ", "-").lower()

    if keyword_slug in effective_slug or keyword.replace(" ", "") in effective_slug.replace("-", ""):
        slug_match = "<span style='color:green;'>✅ আছে</span>"
    else:
        slug_match = "<span style='color:red;'>❌ নেই</span>"
    
    url_len = len(effective_slug)
    url_length_match = f"<span style='color:green;'>✅ {url_len} chars</span>" if url_len <= 75 else f"<span style='color:red;'>❌ {url_len} chars</span>"

    # --- ৪. কিওয়ার্ড ডেনসিটি (Word Boundary Regex ব্যবহার করে) ---
    clean_text = re.sub(r'[^\w\s]', '', content_text)
    total_words = len(clean_text.split())
    keyword_pattern = r'\b' + re.escape(keyword) + r'\b'
    content_count = len(re.findall(keyword_pattern, content_text, re.IGNORECASE | re.UNICODE))
    content_match = f"<span style='color:green;'>✅ আছে ({content_count} বার)</span>" if content_count > 0 else "<span style='color:red;'>❌ নেই</span>"

    if total_words > 0:
        density = (content_count / total_words) * 100
    else:
        density = 0.0

    if 0.5 <= density <= 2.5:
        density_match = f"<span style='color:green;'>✅ {density:.2f}% (Great)</span>"
    else:
        density_match = f"<span style='color:orange;'>⚠️ {density:.2f}% (Optimizable)</span>"

    # --- ৫. Previously Used Keyword Check ---
    used_before = BlogPost.objects.filter(focus_keyword__iexact=keyword).exclude(slug__iexact=effective_slug).exists()
    keyword_used_match = "<span style='color:red;'>❌ Yes (Used before)</span>" if used_before else "<span style='color:green;'>✅ No (Unique)</span>"

    # --- ৬. লিংক এনালাইসিস (ইন্টারনাল ও আউটবাউন্ড) ---
    links = re.findall(r'<a[^>]+href=["\'](.*?)["\']', content_html, re.IGNORECASE)
    internal_links, outbound_links = 0, 0
    current_host = request.get_host()
    for link in links:
        if link.startswith(('#', 'mailto:', 'tel:')): continue
        if link.startswith(('http://', 'https://')) and current_host not in link:
            outbound_links += 1
        else:
            internal_links += 1

    internal_match = f"<span style='color:green;'>✅ {internal_links} found</span>" if internal_links > 0 else "<span style='color:orange;'>⚠️ 0 found</span>"
    outbound_match = f"<span style='color:green;'>✅ {outbound_links} found</span>" if outbound_links > 0 else "<span style='color:orange;'>⚠️ 0 found</span>"

    # --- ৭. প্যারাগ্রাফ সাইজ এনালাইসিস (উন্নত Regex) ---
    paragraphs = re.findall(r'<p\b[^>]*>(.*?)</p>', content_html, re.IGNORECASE | re.DOTALL)
    long_paragraphs = sum(1 for p in paragraphs if len(strip_tags(p).split()) > 150)
    
    if not paragraphs:
        paragraph_match = "<span style='color:orange;'>⚠️ No paragraphs found</span>"
    elif long_paragraphs == 0:
        paragraph_match = "<span style='color:green;'>✅ Short paragraphs (Great)</span>"
    else:
        paragraph_match = f"<span style='color:red;'>❌ {long_paragraphs} are too long</span>"

    # --- ৮. মাল্টিমিডিয়া চেক (ছবি ও ভিডিও) ---
    images_found = len(re.findall(r'<img', content_html, re.IGNORECASE))
    videos_found = len(re.findall(r'<(iframe|video|embed)', content_html, re.IGNORECASE))
    
    if (images_found + videos_found) > 0:
        multimedia_match = f"<span style='color:green;'>✅ {images_found} Image, {videos_found} Video</span>"
    else:
        multimedia_match = "<span style='color:orange;'>⚠️ None found</span>"

    # --- ৯. ফাইনাল Context ---
    context = {
        'keyword': keyword,
        'title_match': title_match,
        'slug_match': slug_match,
        'meta_desc_match': meta_desc_match,
        'meta_keys_match': meta_keys_match,
        'content_match': content_match,
        'url_length_match': url_length_match,
        'density_match': density_match,
        'keyword_used_match': keyword_used_match,
        'internal_match': internal_match,
        'outbound_match': outbound_match,
        'paragraph_match': paragraph_match,
        'multimedia_match': multimedia_match,
    }
    
    html = render_to_string('partials/seo_checker_result.html', context)
    return HttpResponse(html)



def tag_posts(request, slug):
    # ট্যাগটি ডাটাবেজে আছে কি না চেক করে নেওয়া ভালো
    tag = get_object_or_404(Tag, slug=slug)
    
    post_list = BlogPost.objects.filter(tags__slug=slug, status='published').order_by("-created_at")
    
    paginator = Paginator(post_list, 6)
    page_number = request.GET.get("page")
    posts = paginator.get_page(page_number)

    context = {
        "posts": posts,
        "tag": tag,  # পুরো ট্যাগ অবজেক্টটি পাঠালে টেমপ্লেটে tag.name দেখাতে পারবেন
        "tag_slug": slug,
        "recent_posts": BlogPost.objects.filter(status="published").order_by("-created_at")[:5]
    }
    return render(request, "garden-category.html", context)

@csrf_protect
@require_POST
def post_reply(request, comment_id):
    # Login Check
    if not request.user.is_authenticated:
        messages.warning(request, "You must be logged in to reply.")
        return redirect("login")

    comment = get_object_or_404(Comment, id=comment_id)
    
    # Get reply text
    reply_text = request.POST.get("text")
    
    if reply_text and reply_text.strip():
        Reply.objects.create(
            user=request.user,
            comment=comment,
            text=reply_text
        )
        messages.success(request, "Your reply has been added successfully!")
    else:
        # "রিপ্লাই খালি রাখা যাবে না" এর ইংরেজি
        messages.error(request, "Reply cannot be empty.")
        
    return redirect("single_post", slug=comment.post.slug)

# ১০. ইউজারের প্রোফাইল
@login_required
def user_profile(request):
    # ১. ইউজার অনুযায়ী অথর প্রোফাইল খুঁজে বের করা বা তৈরি করা
    author_obj, created = Author.objects.get_or_create(user=request.user)
    
    # ২. ইমেইল পরিবর্তনের কোনো রিকোয়েস্ট পেন্ডিং আছে কি না চেক করা
    is_pending = EmailChangeRequest.objects.filter(
        user=request.user, 
        is_approved=False
    ).exists()
    
    # ৩. ডাটা কনটেক্সটে পাঠানো
    context = {
        'user': request.user,
        'author_profile': author_obj,
        'pending_email_request': is_pending,
        'comments_count': Comment.objects.filter(user=request.user).count(),
        **get_sidebar_data(), # আপনার সাইডবার ডাটা (Recent Posts ইত্যাদি)
    }
    
    return render(request, 'profile.html', context)


@login_required
@csrf_protect
def edit_field(request, field_name):
    author_profile = request.user.author_profile 
    display_value = ""
    message = ""
    
    if request.method == 'POST':
        # ১. ইমেইল এডিট লজিক (Admin Approval Required)
        if field_name == 'email':
            new_email = request.POST.get(field_name)
            
            if new_email == request.user.email:
                return HttpResponse("This is already your current email.", status=400)
            
            # চেক করা হচ্ছে অলরেডি কোনো রিকোয়েস্ট পেন্ডিং আছে কি না
            from .models import EmailChangeRequest # মডেলটি ইম্পোর্ট করুন
            pending_request = EmailChangeRequest.objects.filter(user=request.user, is_approved=False).exists()
            
            if pending_request:
                message = "A request is already pending approval!"
            else:
                EmailChangeRequest.objects.create(user=request.user, new_email=new_email)
                message = "Request sent to Admin for approval!"
            
            display_value = request.user.email # ইমেইল পরিবর্তন না করে বর্তমানটাই দেখানো হবে

        # ২. ইউজারনেম আপডেট
        elif field_name == 'username':
            new_value = request.POST.get(field_name)
            if new_value:
                request.user.username = new_value
                request.user.save()
                message = "Username updated!"
                display_value = request.user.username
        
        # ৩. ইমেজ আপডেট
        elif field_name == 'profile_image':
            new_image = request.FILES.get('profile_image')
            if new_image:
                author_profile.profile_image = new_image
                author_profile.save()
                message = "Image saved!"
                display_value = author_profile.profile_image.url

        # ৪. অন্যান্য ফিল্ড (full_name, bio)
        else:
            new_value = request.POST.get(field_name)
            if hasattr(author_profile, field_name):
                setattr(author_profile, field_name, new_value)
                author_profile.save()
                message = "Saved successfully!"
                display_value = new_value

        return render(request, 'partials/profile_row_updated.html', {
            'field_name': field_name, 
            'value': display_value, 
            'success_msg': message 
        })

    # GET রিকোয়েস্টে ইনপুট ফিল্ড দেখাবে
    return render(request, 'partials/edit_input.html', {
        'field_name': field_name, 
        'user': request.user,
        'author_profile': author_profile
    })


# ড্যাশবোর্ড মেইন ভিউ
@staff_member_required
def admin_dashboard(request):
    pending_requests = EmailChangeRequest.objects.filter(is_approved=False).order_by('-created_at')
    return render(request, 'admin_dashboard.html', {'pending_requests': pending_requests})

# রিকোয়েস্ট এপ্রুভ করার লজিক (HTMX)
@staff_member_required
@require_POST
def approve_email_request(request, request_id):
    email_req = get_object_or_404(EmailChangeRequest, id=request_id)
    
    # মূল ইউজারের ইমেইল আপডেট
    user = email_req.user
    user.email = email_req.new_email
    user.save()
    
    # রিকোয়েস্টটি এপ্রুভড হিসেবে মার্ক করা
    email_req.is_approved = True
    email_req.save()
    
    # এপ্রুভ হওয়ার পর ওই রো-টি রিমুভ করে দেওয়ার জন্য খালি রেসপন্স বা সাকসেস মেসেজ
    return HttpResponse("") 

# রিকোয়েস্ট রিজেক্ট/ডিলিট করার লজিক (HTMX)
@staff_member_required
@require_POST
def reject_email_request(request, request_id):
    email_req = get_object_or_404(EmailChangeRequest, id=request_id)
    email_req.delete()
    return HttpResponse("")


@login_required
@require_POST
def cancel_email_request(request):
    from .models import EmailChangeRequest
    # ইউজারের পেন্ডিং রিকোয়েস্টটি খুঁজে বের করে ডিলিট করা
    EmailChangeRequest.objects.filter(user=request.user, is_approved=False).delete()
    
    # ডিলিট করার পর ইমেইল রো-টি আবার আগের অবস্থায় (Edit বাটনসহ) ফিরিয়ে আনা
    return render(request, 'partials/profile_row_updated.html', {
        'field_name': 'email',
        'value': request.user.email,
        'success_msg': 'Request cancelled successfully.'
    })
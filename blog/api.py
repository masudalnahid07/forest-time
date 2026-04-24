import os
from typing import List, Optional
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from ninja.security import APIKeyHeader
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.core.files.storage import default_storage # নতুন ইম্পোর্ট
from .models import BlogPost, Category, Author

# --- ১. অথেন্টিকেশন ---
class ApiKeyAuth(APIKeyHeader):
    param_name = "X-API-KEY"
    def authenticate(self, request, key):
        if key == os.getenv("NINJA_API_KEY"):
            return key

api = NinjaAPI(auth=ApiKeyAuth(), version="v2")

# --- ২. ডাটা দেখার জন্য Schema (GET) ---
class BlogPostSchema(Schema):
    id: int
    title: str
    slug: str
    post_type: str
    category_id: Optional[int] = None
    feature_img: Optional[str] = None
    status: str
    views_count: int

    @staticmethod
    def resolve_feature_img(obj):
        if obj.feature_img:
            return obj.feature_img.url
        return None

# --- ৩. ডাটা পাঠানোর জন্য Schema (POST) ---
class BlogPostIn(Schema):
    title: str
    slug: Optional[str] = None
    feature_img_path: Optional[str] = None  # <--- ইমেজ পাথ নেওয়ার জন্য নতুন ফিল্ড
    post_type: str = 'info'
    category_id: Optional[int] = None
    author_id: Optional[int] = None
    post_details: str
    status: str = 'draft'
    focus_keyword: Optional[str] = None
    meta_keywords: Optional[str] = None
    meta_description: Optional[str] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_url: Optional[str] = None
    rating_value: Optional[float] = 4.5

# --- ৪. এন্ডপয়েন্টসমূহ ---

# সব পোস্ট দেখা
@api.get("/posts", response=List[BlogPostSchema])
def list_posts(request):
    return BlogPost.objects.all().order_by('-created_at')

# [নতুন] মিডিয়া আপলোড এন্ডপয়েন্ট (ওয়ার্ডপ্রেস লজিক)
@api.post("/upload-media")
def upload_media(request, file: UploadedFile = File(...)):
    # ফাইলটি মিডিয়া ফোল্ডারে সেভ হবে
    path = default_storage.save(f"feature_images/{file.name}", file)
    return {"image_path": path}

# নতুন পোস্ট তৈরি করা
@api.post("/create-posts")
def create_post(request, data: BlogPostIn):
    try:
        category = Category.objects.filter(id=data.category_id).first() if data.category_id else None
        author = Author.objects.filter(id=data.author_id).first() if data.author_id else None
        
        post_data = data.dict()
        
        # রিলেশনশিপ ফিল্ডগুলো পপ করা
        img_path = post_data.pop('feature_img_path', None)
        post_data.pop('category_id', None)
        post_data.pop('author_id', None)
        
        # পোস্ট অবজেক্ট তৈরি
        post = BlogPost(**post_data)
        post.category = category
        post.author = author
        
        # যদি ইমেজ পাথ থাকে তবে তা সেভ করা
        if img_path:
            post.feature_img = img_path
            
        post.save()
        
        return {"id": post.id, "message": "Success"}
    except IntegrityError:
        return api.create_response(request, {"message": "Title/Slug already exists!"}, status=400)

# (পুরাতন) সরাসরি ইমেজ আপলোড এন্ডপয়েন্টটিও রেখে দিলাম যদি প্রয়োজন হয়
@api.post("/posts/{post_id}/upload-image")
def upload_post_image(request, post_id: int, file: UploadedFile = File(...)):
    post = get_object_or_404(BlogPost, id=post_id)
    post.feature_img = file
    post.save()
    return {"message": "Image uploaded successfully", "image_url": post.feature_img.url}
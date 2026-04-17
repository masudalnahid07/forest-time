import os
from typing import List, Optional
from ninja import NinjaAPI, Schema, File
from ninja.files import UploadedFile
from ninja.security import APIKeyHeader
from django.shortcuts import get_object_or_404
from .models import BlogPost, Category, Author
from ninja import File, UploadedFile

# ১. Authentication (.env থেকে)
class ApiKeyAuth(APIKeyHeader):
    param_name = "X-API-KEY"
    def authenticate(self, request, key):
        if key == os.getenv("NINJA_API_KEY"):
            return key

api = NinjaAPI(auth=ApiKeyAuth(), version="v2")

# ২. Schemas (ডাটা ফরম্যাট)
class BlogPostSchema(Schema):
    id: int
    title: str
    slug: str
    post_type: str
    category_id: Optional[int] = None
    # ইমেজ ফিল্ডটি এখানে যোগ করা হলো
    feature_img: Optional[str] = None 
    focus_keyword: Optional[str] = None
    meta_description: Optional[str] = None
    status: str
    views_count: int

    # ইমেজ ফিল্ডের ফুল URL পাওয়ার জন্য এই মেথডটি সাহায্য করবে
    @staticmethod
    def resolve_feature_img(obj):
        if obj.feature_img:
            return obj.feature_img.url
        return None

# ৩. POST করার জন্য Schema
class BlogPostIn(Schema):
    title: str
    post_type: str = 'info'
    category_id: Optional[int] = None
    author_id: Optional[int] = None
    post_details: str
    status: str = 'draft'
    slug: Optional[str] = None # আপনি যদি স্লাগও পাঠাতে চান
    focus_keyword: Optional[str] = None
    meta_keywords: Optional[str] = None
    meta_description: Optional[str] = None
    product_name: Optional[str] = None
    product_price: Optional[float] = None
    product_url: Optional[str] = None
    rating_value: Optional[float] = 4.5

# --- এন্ডপয়েন্টসমূহ ---

# সব পোস্ট দেখার জন্য (GET)
@api.get("/posts", response=List[BlogPostSchema])
def list_posts(request):
    # লেটেস্ট পোস্ট আগে দেখানোর জন্য order_by ব্যবহার করা ভালো
    return BlogPost.objects.all().order_by('-created_at')

# নতুন পোস্ট করার জন্য (POST)
@api.post("/posts")
def create_post(request, data: BlogPostIn):
    category = None
    if data.category_id:
        category = get_object_or_404(Category, id=data.category_id)
        
    author = None
    if data.author_id:
        author = get_object_or_404(Author, id=data.author_id)
    
    post_data = data.dict()
    # pop করার সময় default None দিন যাতে কি (key) না থাকলে এরর না দেয়
    post_data.pop('category_id', None) 
    post_data.pop('author_id', None)
    
    post = BlogPost.objects.create(
        **post_data, 
        category=category, 
        author=author
    )
    return {"id": post.id, "message": "Success"}

# ৪. ইমেজ আপলোড
@api.post("/posts/{post_id}/upload-image")
def upload_post_image(request, post_id: int, file: UploadedFile = File(...)):
    post = get_object_or_404(BlogPost, id=post_id)
    post.feature_img = file
    post.save()
    return {"message": "Image uploaded successfully", "image_url": post.feature_img.url}
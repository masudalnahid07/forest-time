import os
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field as RichTextField
from taggit.managers import TaggableManager
from django.contrib.auth import get_user_model
from django.db.models import Count
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver 

User = get_user_model()

# --- ইমেজ প্রসেসিং হেল্পার ফাংশন ---
def compress_and_convert_to_webp(image_field):
    if not image_field:
        return image_field
        
    img = Image.open(image_field)
    
    # RGBA বা P মোড থাকলে RGB তে কনভার্ট (WebP এর জন্য নিরাপদ)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    output = BytesIO()
    
    # আপনার হোমপেজ ও সিঙ্গেল পেজের সাইজ অনুযায়ী ১০০০px সেফ উইডথ
    max_width = 1000 
    
    if img.width > max_width:
        output_size = (max_width, int((max_width / img.width) * img.height))
        img = img.resize(output_size, Image.LANCZOS)
    
    # WebP ফরম্যাটে সেভ (৮৫% কোয়ালিটি সাইট ফাস্ট রাখবে)
    img.save(output, format='WEBP', quality=85)
    output.seek(0)
    
    name = os.path.splitext(image_field.name)[0] + '.webp'
    return ContentFile(output.read(), name=name)


# --- অথর প্রোফাইল মডেল ---
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    bio = RichTextField(config_name="extends")
    profile_image = models.ImageField(upload_to="profiles/%Y/%m/%d/", null=True, blank=True)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if self.profile_image:
            self.profile_image = compress_and_convert_to_webp(self.profile_image)
        super().save(*args, **kwargs)


# --- ব্লগ মেটা মডেল ---
class BlogMeta(models.Model):
    blog_title = models.CharField(max_length=250)
    blog_details = models.TextField()

    class Meta:
        verbose_name = "Blog Meta"
        verbose_name_plural = "Blog Meta"

    def __str__(self):
        return self.blog_title


# --- ক্যাটাগরি মডেল (Sitemap এরর ফিক্স সহ) ---
class Category(models.Model):
    category_title = models.CharField(max_length=250, unique=True)
    category_slug = models.SlugField(max_length=250, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["category_title"]

    def get_absolute_url(self):
            # 'category_slug' এর বদলে শুধু 'slug' ব্যবহার করুন
            return reverse("category", kwargs={"slug": self.category_slug})

    def __str__(self):
        if self.parent:
            return f"{self.parent.category_title} → {self.category_title}"
        return self.category_title

    def save(self, *args, **kwargs):
        if self.category_title:
            self.category_title = self.category_title.title()
        if not self.category_slug:
            self.category_slug = slugify(self.category_title)
        
        # ইউনিক স্লাগ চেক লজিক
        original_slug = self.category_slug
        counter = 1
        while Category.objects.filter(category_slug=self.category_slug).exclude(pk=self.pk).exists():
            self.category_slug = f"{original_slug}-{counter}"
            counter += 1
        super().save(*args, **kwargs)


# --- মেইন ব্লগ পোস্ট মডেল ---
class BlogPost(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("published", "Published")]
    POST_TYPE_CHOICES = [('info', 'Informative (BlogPosting)'), ('review', 'Product Review (Review)')]

    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPE_CHOICES, default='info')
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, related_name="posts")
    feature_img = models.ImageField(upload_to="images/%Y/%m/%d/", null=True, blank=True)
    
    # SEO & Review Fields
    focus_keyword = models.CharField(max_length=500, blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    product_name = models.CharField(max_length=250, blank=True, null=True)
    product_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    product_url = models.URLField(blank=True, null=True)
    rating_value = models.FloatField(default=4.5, blank=True, null=True)

    post_details = RichTextField(config_name="extends")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    author = models.ForeignKey('Author', on_delete=models.SET_NULL, null=True, related_name="posts")
    tags = TaggableManager(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def get_absolute_url(self):
        return reverse("single_post", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.title()
        if not self.slug:
            self.slug = slugify(self.title)
        
        # ইউনিক স্লাগ চেক
        original_slug = self.slug
        counter = 1
        while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        # ইমেজ অপ্টিমাইজেশন (শুধু নতুন ইমেজ বা ইমেজ পরিবর্তন হলে কনভার্ট হবে)
        if self.feature_img:
            try:
                this = BlogPost.objects.get(pk=self.pk)
                if this.feature_img != self.feature_img:
                    self.feature_img = compress_and_convert_to_webp(self.feature_img)
            except BlogPost.DoesNotExist:
                self.feature_img = compress_and_convert_to_webp(self.feature_img)
            
        super().save(*args, **kwargs)


# --- কমেন্ট ও রিপ্লাই মডেল ---
class Comment(models.Model):
    user = models.ForeignKey(User, related_name="user_comments", on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class Reply(models.Model):
    user = models.ForeignKey(User, related_name="user_replies", on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, related_name="replies", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Replies"

    def __str__(self):
        return f"Reply by {self.user.username}"
    

# ১. প্রোফাইল মডেল (ইউজারের অতিরিক্ত তথ্যের জন্য)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='profile_pics', default='default_user.png', blank=True)
    bio = models.TextField(max_length=500, blank=True)
    full_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

# ২. সিগন্যাল (নতুন ইউজার তৈরি হলে অটোমেটিক প্রোফাইল তৈরি করার জন্য)
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
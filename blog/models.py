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
    
    try:
        img = Image.open(image_field)
        
        # ট্রান্সপারেন্সি বজায় রাখা
        if img.mode == "P":
            img = img.convert("RGBA")
            
        output = BytesIO()
        max_width = 1000 
        
        if img.width > max_width:
            output_size = (max_width, int((max_width / img.width) * img.height))
            img = img.resize(output_size, Image.Resampling.LANCZOS)
        
        # SEO এর জন্য method=6 এবং কোয়ালিটি ৮৫
        img.save(output, format='WEBP', quality=85, method=6)
        output.seek(0)
        
        # ফাইল নেম ক্লিন করা
        file_name = os.path.basename(image_field.name)
        name = os.path.splitext(file_name)[0] + '.webp'
        
        return ContentFile(output.read(), name=name)
        
    except Exception as e:
        print(f"Image processing error: {e}")
        return image_field


# --- অথর প্রোফাইল মডেল ---
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    full_name = models.CharField(max_length=100, blank=True, help_text="Type your full name")
    author_image = models.ImageField(
        upload_to="profiles/%Y/%m/%d/",
        null=True,
        blank=True,
        default='upload/user_defult.jpeg',
    )
    bio = RichTextField(config_name="extends", blank=True, null=True)

    def __str__(self):
        return self.full_name if self.full_name else self.user.username

    def save(self, *args, **kwargs):
        # ১. ইমেজ এবং ডিফল্ট নাম চেক
        if self.author_image and 'user_defult.jpeg' not in self.author_image.name:
            try:
                if self.pk:
                    # ডাটাবেস থেকে পুরাতন অবজেক্টটি আনা
                    old_instance = Author.objects.filter(pk=self.pk).first()
                    
                    if old_instance and old_instance.author_image != self.author_image:
                        # নতুন ইমেজকে WebP তে কনভার্ট করা
                        self.author_image = compress_and_convert_to_webp(self.author_image)
                        
                        # ২. পুরাতন ফাইল ডিলিট করার নিরাপদ উপায় (Storage API)
                        if old_instance.author_image and 'user_defult.jpeg' not in old_instance.author_image.name:
                            try:
                                # storage এবং name আলাদাভাবে ডিফাইন করা
                                img_storage = getattr(old_instance.author_image, 'storage', None)
                                img_name = old_instance.author_image.name 
                                if img_storage and img_storage.exists(img_name):    
                                    img_storage.delete(img_name)

                            except Exception:
                                pass
                else:
                    # নতুন প্রোফাইলের জন্য ইমেজ কনভার্ট
                    self.author_image = compress_and_convert_to_webp(self.author_image)
                    
            except Exception as e:
                print(f"Error in save method: {e}")
        
        # ৩. সব কন্ডিশনের বাইরে সেভ কল করা
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


# --- ক্যাটাগরি মডেল ---
class Category(models.Model):
    category_title = models.CharField(max_length=250, unique=True)
    category_slug = models.SlugField(max_length=250, unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["category_title"]

    def get_absolute_url(self):
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

    @property
    def alt_text_from_slug(self):
        return self.slug.replace('-', ' ').title()
    
    @property
    def clean_alt_text(self):
        if self.focus_keyword:
            return self.focus_keyword
        return self.slug.replace('-', ' ').title()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # ১. টাইটেল এবং স্লাগ অটো-জেনারেট লজিক
        if self.title:
            self.title = self.title.title()
        if not self.slug:
            self.slug = slugify(self.title)
        
        # ইউনিক স্লাগ নিশ্চিত করা
        original_slug = self.slug
        counter = 1
        while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        # ২. ইমেজ অপ্টিমাইজেশন এবং ডিলিট লজিক
        if self.feature_img:
            try:
                if self.pk:
                    # ডাটাবেস থেকে পুরাতন পোস্টটি আনা
                    old_post = BlogPost.objects.filter(pk=self.pk).first()
                    
                    if old_post and old_post.feature_img != self.feature_img:
                        # নতুন ছবিকে WebP তে কনভার্ট করা
                        self.feature_img = compress_and_convert_to_webp(self.feature_img)
                        
                        # পুরাতন ছবি সার্ভার থেকে ডিলিট করা (নেমচিপ হোস্টিংয়ের জন্য জরুরি)
                        if old_post.feature_img:
                            try:
                                img_storage = getattr(old_post.feature_img, 'storage', None)
                                img_name = old_post.feature_img.name
                                if img_storage and img_storage.exists(img_name):
                                    img_storage.delete(img_name)
                            except Exception:
                                pass
                else:
                    # একদম নতুন পোস্টের ক্ষেত্রে ছবি কনভার্ট করা
                    self.feature_img = compress_and_convert_to_webp(self.feature_img)
                    
            except Exception as e:
                print(f"BlogPost image optimization error: {e}")
        
        # ৩. মেইন সেভ মেথড কল করা
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


# --- প্রোফাইল মডেল ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='profile_pics/%Y/%m/%d/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    full_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        # প্রোফাইল ইমেজ অপ্টিমাইজেশন এবং ডিলিট লজিক
        if self.image:
            try:
                if self.pk:
                    # ডাটাবেস থেকে পুরাতন প্রোফাইলটি আনা
                    old_profile = Profile.objects.filter(pk=self.pk).first()
                    
                    if old_profile and old_profile.image != self.image:
                        # নতুন ছবিকে WebP তে কনভার্ট করা
                        self.image = compress_and_convert_to_webp(self.image)
                        
                        # পুরাতন ছবি সার্ভার থেকে ডিলিট করা
                        if old_profile.image:
                            try:
                                img_storage = getattr(old_profile.image, 'storage', None)
                                img_name = old_profile.image.name
                                if img_storage and img_storage.exists(img_name):
                                    img_storage.delete(img_name)
                            except Exception:
                                pass
                else:
                    # একদম নতুন প্রোফাইলের ক্ষেত্রে ছবি কনভার্ট করা
                    self.image = compress_and_convert_to_webp(self.image)
                    
            except Exception as e:
                print(f"Profile image optimization error: {e}")
        
        # মেইন সেভ মেথড কল করা
        super().save(*args, **kwargs)


# --- সিগন্যালস (নিরাপদ লজিক) ---
@receiver(post_save, sender=User)
def create_or_update_user_profiles(sender, instance, created, **kwargs):
    if created:
        # নতুন ইউজার তৈরি হলে প্রোফাইল এবং অথর অবজেক্ট তৈরি হবে
        # get_or_create ব্যবহার করা নিরাপদ যাতে ডুপ্লিকেট না হয়
        Profile.objects.get_or_create(user=instance)
        Author.objects.get_or_create(user=instance)
    
    # নোট: এখানে else ব্লকে প্রোফাইল .save() কল করার দরকার নেই। 
    # এতে ইমেজ প্রসেসিং লজিক বারবার ট্রিগার হওয়ার ঝুঁকি থাকে।


class EmailChangeRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    new_email = models.EmailField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} wants to change email to {self.new_email}"
    

#--- স্ট্যাটিক পেজ মডেল  শুরু---
class StaticPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, help_text="উদা: about-us, privacy-policy")
    content = RichTextField(config_name="extends") 
    meta_description = models.CharField(max_length=160, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # নতুন ফিল্ড: পেইজের সিরিয়াল মেনটেইন করার জন্য
    order = models.PositiveIntegerField(default=0, help_text="পেইজটি কোন সিরিয়ালে থাকবে (যেমন: ১, ২, ৩)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Static Page"
        verbose_name_plural = "Static Pages"
        ordering = ['order', 'title'] # এটি ডাটাবেস লেভেলে সিরিয়াল ঠিক রাখবে

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('static_page', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.title()
        if not self.slug:
            self.slug = slugify(self.title)
        
        original_slug = self.slug
        counter = 1
        while StaticPage.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
        super().save(*args, **kwargs)

#--- স্ট্যাটিক পেজ মডেল শেষ---
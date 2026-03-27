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
    
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    output = BytesIO()
    max_width = 1000 
    
    if img.width > max_width:
        output_size = (max_width, int((max_width / img.width) * img.height))
        img = img.resize(output_size, Image.LANCZOS)
    
    img.save(output, format='WEBP', quality=85)
    output.seek(0)
    
    name = os.path.splitext(image_field.name)[0] + '.webp'
    return ContentFile(output.read(), name=name)


# --- অথর প্রোফাইল মডেল ---
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    full_name = models.CharField(max_length=100, blank=True, help_text="Type your full name")
    author_image = models.ImageField(
    upload_to="profiles/%Y/%m/%d/",
    null=True,
    blank=True,
    default='upload/user_defult.jpeg',  # তাহলে MEDIA_ROOT/upload/user_defult.jpeg এ ফাইল দরকার
)
    bio = RichTextField(config_name="extends", blank=True, null=True)

    def __str__(self):
        return self.full_name if self.full_name else self.user.username

    def save(self, *args, **kwargs):
        # ইমেজ ফিল্ডের নাম 'author_image' অনুযায়ী লজিক ফিক্স করা হয়েছে
        if self.author_image and 'user_defult.jpeg' not in self.author_image.name:
            try:
                if not self.pk:
                    self.author_image = compress_and_convert_to_webp(self.author_image)
                else:
                    old_instance = Author.objects.get(pk=self.pk)
                    if old_instance.author_image != self.author_image:
                        self.author_image = compress_and_convert_to_webp(self.author_image)
            except Exception:
                pass
        
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
        if self.title:
            self.title = self.title.title()
        if not self.slug:
            self.slug = slugify(self.title)
        
        original_slug = self.slug
        counter = 1
        while BlogPost.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1
        
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


# --- প্রোফাইল মডেল ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to='profile_pics', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    full_name = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'


# --- সিগন্যালস ---
@receiver(post_save, sender=User)
def create_or_update_user_profiles(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
        Author.objects.create(user=instance)
    else:
        if hasattr(instance, 'profile'):
            instance.profile.save()
        if hasattr(instance, 'author_profile'):
            instance.author_profile.save()


class EmailChangeRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    new_email = models.EmailField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} wants to change email to {self.new_email}"
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field as RichTextField
from taggit.managers import TaggableManager
from django.contrib.auth import get_user_model

User = get_user_model()

class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="author_profile")
    bio = RichTextField(config_name="extends")
    profile_image = models.ImageField(
        upload_to="profiles/%Y/%m/%d/", null=True, blank=True
    )

    def __str__(self):
        return self.user.username


class BlogMeta(models.Model):
    blog_title = models.CharField(max_length=250)
    blog_details = models.TextField()

    class Meta:
        verbose_name = "Blog Meta"
        verbose_name_plural = "Blog Meta"

    def __str__(self):
        return self.blog_title


class Category(models.Model):
    category_title = models.CharField(max_length=250, unique=True)
    category_slug = models.SlugField(max_length=250, unique=True, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["category_title"]

    def __str__(self):
        return self.category_title

    def save(self, *args, **kwargs):
        if self.category_title:
            self.category_title = self.category_title.title()
        
        # Determine base slug
        if not self.category_slug:
            self.category_slug = slugify(self.category_title)
        else:
            self.category_slug = slugify(self.category_slug)

        # Unique slug logic
        original_slug = self.category_slug
        queryset = Category.objects.all().exclude(pk=self.pk)
        counter = 1
        while queryset.filter(category_slug=self.category_slug).exists():
            self.category_slug = f"{original_slug}-{counter}"
            counter += 1

        super().save(*args, **kwargs)


class BlogPost(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("published", "Published"),
    ]
    
    # পোস্টের ধরন নির্ধারণের জন্য (Schema-র জন্য গুরুত্বপূর্ণ)
    POST_TYPE_CHOICES = [
        ('info', 'Informative (BlogPosting)'),
        ('review', 'Product Review (Review)'),
    ]

    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    
    # স্কিমা এবং ক্যাটাগরি ডাটা
    post_type = models.CharField(max_length=10, choices=POST_TYPE_CHOICES, default='info')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    
    # ইমেজ ও এসইও ফিল্ড
    feature_img = models.ImageField(upload_to="images/%Y/%m/%d/", null=True, blank=True)
    focus_keyword = models.CharField(max_length=500, blank=True, null=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    meta_description = models.TextField(max_length=500, blank=True)
    
    # রিভিউ পোস্টের জন্য অতিরিক্ত ফিল্ড (Product Schema)
    product_name = models.CharField(max_length=250, blank=True, null=True, help_text="রিভিউ পোস্ট হলে প্রোডাক্টের নাম দিন")
    product_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, help_text="প্রোডাক্টের দাম (USD)")
    product_url = models.URLField(blank=True, null=True, help_text="অ্যাফিলিয়েট বা প্রোডাক্ট লিংক")
    rating_value = models.FloatField(default=4.5, blank=True, null=True, help_text="রেটিং (১ থেকে ৫ এর মধ্যে)")

    # কন্টেন্ট ও অন্যান্য
    post_details = RichTextField(config_name="extends")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="draft")
    author = models.ForeignKey(
        Author, on_delete=models.SET_NULL, null=True, related_name="posts"
    )
    tags = TaggableManager(blank=True)
    
    # ট্র্যাকিং ও সময়
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # টাইটেল ফরমেটিং
        if self.title:
            self.title = self.title.title()
            
        # অটো স্লাগ জেনারেশন ও ডুপ্লিকেট চেক
        if not self.slug:
            self.slug = slugify(self.title)
        else:
            self.slug = slugify(self.slug)

        original_slug = self.slug
        queryset = BlogPost.objects.all().exclude(pk=self.pk)
        counter = 1
        while queryset.filter(slug=self.slug).exists():
            self.slug = f"{original_slug}-{counter}"
            counter += 1

        super().save(*args, **kwargs)


class Comment(models.Model):
    user = models.ForeignKey(
        User, related_name="user_comments", on_delete=models.CASCADE
    )
    post = models.ForeignKey(
        BlogPost, related_name="comments", on_delete=models.CASCADE
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class Reply(models.Model):
    user = models.ForeignKey(
        User, related_name="user_replies", on_delete=models.CASCADE
    )
    comment = models.ForeignKey(
        Comment, related_name="replies", on_delete=models.CASCADE
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Replies"

    def __str__(self):
        return f"Reply by {self.user.username}"
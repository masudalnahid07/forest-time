from random import choice
from tarfile import NUL
from turtle import title
from django.db import models
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field as RichTextField
from taggit.managers import TaggableManager
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()
class Author(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = RichTextField(config_name='extends')
    profile_image = models.ImageField(upload_to="profiles/%Y/%m/%d/", null=True, blank=True)

    def __str__(self):
        return self.user.username

class BlogMeta(models.Model):
    blog_title = models.CharField(max_length=250)
    blog_details=models.TextField()

    def __str__(self):
        return self.blog_title

class Category(models.Model):
    category_title = models.CharField(max_length=250, unique=True)
    category_slug = models.SlugField(max_length=250, unique=True, blank=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['category_title']

    def __str__(self):
        return self.category_title

    def save(self, *args, **kwargs):

        # Title কে title case করে নাও
        if self.category_title:
            self.category_title = self.category_title.title()

        # যদি slug ফিল্ড blank থাকে → title থেকে নিবে
        if not self.category_slug:
            self.category_slug = slugify(self.category_title)
        else:
            # যদি slug ফিল্ডে কিছু লেখা থাকে → clean করবে
            self.category_slug = slugify(self.category_slug)

        base_slug = self.category_slug
        slug = base_slug
        counter = 1

        # Duplicate check (নিজের instance বাদ দিয়ে)
        while Category.objects.filter(category_slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.category_slug = slug

        super().save(*args, **kwargs)

class BlogPost(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    title = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    category = models.ForeignKey('Category',on_delete=models.SET_NULL,null=True,related_name='posts')
    feature_img = models.ImageField(upload_to='images/%Y/%m/%d/',null=True,blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    meta_description = models.CharField(max_length=500, blank=True,unique=True)
    post_details = RichTextField(config_name='extends')
    status = models.CharField(max_length=10,choices=STATUS_CHOICES,default='draft')
    author = models.ForeignKey('Author',on_delete=models.SET_NULL,null=True,related_name='posts')
    tags = TaggableManager(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)
    class Meta:
        ordering = ['-created_at']
    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Title কে Title Case বানানো
        if self.title:
            self.title = self.title.title()
        # যদি slug ফাঁকা থাকে → title থেকে auto slug বানাবে
        if not self.slug:
            base_slug = slugify(self.title)
        else:
            # যদি slug দেওয়া থাকে → clean করবে
            base_slug = slugify(self.slug)
        slug = base_slug
        counter = 1
        # Duplicate check (নিজের instance বাদ দিয়ে)
        while BlogPost.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug
        super().save(*args, **kwargs)

class Comment(models.Model):
    user = models.ForeignKey(User, related_name="User_comments", on_delete=models.CASCADE)
    post = models.ForeignKey(BlogPost,related_name="post_comments", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.text

class Reply(models.Model):
    user = models.ForeignKey(User, related_name="User_Replies", on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment,related_name="Comment_Reply", on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.text
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

# CKEditor 5 এর উইজেট এবং আপনার মডেল ইম্পোর্ট
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import BlogPost 

# ==========================================
# 1. Registration Form
# ==========================================
class CustomRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get("email")

        # স্প্যাম/টেম্পোরারি ইমেইল ডোমেইনের একটি লিস্ট
        blocked_domains = [
            "tempmail.com",
            "10minutemail.com",
            "mailinator.com",
            "guerrillamail.com",
        ]

        domain = email.split("@")[1]

        if domain in blocked_domains:
            raise ValidationError(
                "এই ইমেইল প্রোভাইডার দিয়ে রেজিস্ট্রেশন করা যাবে না। দয়া করে সঠিক ইমেইল দিন।"
            )

        # ইমেইলটি আগে থেকে ডাটাবেসে আছে কিনা চেক করা
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "এই ইমেইলটি দিয়ে ইতিমধ্যে একটি অ্যাকাউন্ট তৈরি করা হয়েছে।"
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


# ==========================================
# 2. Article Edit Form (with CKEditor 5)
# ==========================================
class PostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'category', 'feature_img', 'post_details', 'tags']
        
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            
            # CKEditor5Widget যুক্ত করা হয়েছে
            'post_details': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends" 
            ),
            
            'feature_img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
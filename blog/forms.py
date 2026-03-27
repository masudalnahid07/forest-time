from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

# CKEditor 5 এর উইজেট এবং আপনার মডেল ইম্পোর্ট
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import BlogPost, Profile 

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
                "This email provider is not allowed. Please use a valid email address."
            )

        # ইমেইলটি আগে থেকে ডাটাবেসে আছে কিনা চেক করা
        if User.objects.filter(email=email).exists():
            raise ValidationError(
                "This email is already associated with an account."
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
            
            # CKEditor5Widget যুক্ত করা হয়েছে
            'post_details': CKEditor5Widget(
                attrs={"class": "django_ckeditor_5"}, config_name="extends" 
            ),
            
            'feature_img': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


# ==========================================
# 3. User & Profile Update Forms
# ==========================================

# ইউজারের বেসিক তথ্য (ইমেইল বাদে) আপডেট করার ফর্ম
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

# প্রোফাইল পিকচার এবং বায়ো আপডেট করার ফর্ম
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'image', 'bio']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your Full Name'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us about yourself...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
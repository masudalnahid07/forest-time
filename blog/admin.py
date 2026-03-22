from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import path
from django.http import JsonResponse
from .models import *

# Register your models here.
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Reply)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status_button", "created_at"]
    list_filter = ["status", "category", "author", "created_at"]
    search_fields = ["title", "focus_keyword", "category__category_title"]
    
    # নতুন ফিল্ডটি জ্যাংগো অ্যাডমিন প্যানেলে দেখানোর জন্য
    readonly_fields = ['seo_analyzer']

    # HTMX বাটন এবং রেজাল্ট বক্সের ডিজাইন
    def seo_analyzer(self, obj):
        return mark_safe(
            '''
            <div id="seo-result-box" style="margin-bottom: 15px; min-height: 50px;">
                <span style="color: #888; font-style: italic;">
                    পুরানো বা নতুন আর্টিকেলের SEO স্কোর দেখতে নিচের বাটনে ক্লিক করুন:
                </span>
            </div>
            
            <button type="button"
                    id="seo-check-btn"
                    hx-post="/live-seo-checker/"
                    hx-include="closest form"
                    hx-target="#seo-result-box"
                    style="background: #17a2b8; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold; transition: 0.3s;">
                🔍 Check SEO Match
            </button>
            
            <script>
                // বাটন ক্লিক করলে ডাটা আপডেট হবে
                document.getElementById('seo-check-btn').addEventListener('click', function() {
                    // CKEditor ডাটা সিঙ্ক (পুরাতন আর্টিকেলের জন্য জরুরি)
                    if (typeof CKEDITOR !== 'undefined') {
                        for (var instance in CKEDITOR.instances) {
                            CKEDITOR.instances[instance].updateElement();
                        }
                    }
                    // TinyMCE যদি থাকে
                    if (typeof tinymce !== 'undefined') {
                        tinymce.triggerSave();
                    }
                });

                // HTMX রিকোয়েস্ট পাঠানোর ঠিক আগ মুহূর্তে ডাটা রিফ্রেশ করা
                document.body.addEventListener('htmx:configRequest', function(evt) {
                    if (typeof CKEDITOR !== 'undefined' && CKEDITOR.instances['id_post_details']) {
                        CKEDITOR.instances['id_post_details'].updateElement();
                    }
                });
            </script>
            '''
        )
    seo_analyzer.short_description = "SEO Live Analyzer"

    def status_button(self, obj):
        # সেফটি চেক: যদি নতুন পোস্ট তৈরি করার সময় অবজেক্ট সেভ না থাকে
        if not obj or not obj.id:
            return "-"
            
        if obj.status == "published":
            bg_color = "#28a745" # Green
            btn_text = "Published"
        else:
            bg_color = "#ffc107" # Yellow
            btn_text = "Draft"
            
        return format_html(
            '<button type="button" style="background-color: {}; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; font-weight: bold;" '
            'hx-post="/toggle-status/{}/" hx-swap="outerHTML">{}</button>',
            bg_color, obj.id, btn_text
        )
    status_button.short_description = "Status"
        
    class Media:
        js = (
            'https://unpkg.com/htmx.org@1.9.10',
            'js/keyword_counter.js',
        )
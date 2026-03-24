from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import *

# ১. সাধারণ মডেলগুলো রেজিস্টার
admin.site.register(Author)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Reply)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    # list_display তে 'view_post_link' কলামটি যোগ করা হয়েছে সরাসরি ওয়েবসাইট থেকে দেখার জন্য
    list_display = ["title", "category", "status_button", "view_post_link", "created_at"]
    list_filter = ["status", "category", "author", "created_at"]
    search_fields = ["title", "focus_keyword", "category__category_title"]
    
    # টাইটেল লিখলে অটো স্ল্যাগ জেনারেট হবে (Wordpress এর মতো সুবিধা)
    prepopulated_fields = {"slug": ("title",)}
    
    # এডিট পেজে ফিল্ডগুলোকে সুন্দরভাবে সেকশন অনুযায়ী সাজানো (Fieldsets)
    fieldsets = (
        ("Basic Information", {
            "fields": ("title", "slug", "category", "post_type", "author", "feature_img")
        }),
        ("Article Content", {
            "fields": ("post_details",),
        }),
        ("SEO & Meta Settings", {
            "fields": ("focus_keyword", "meta_keywords", "meta_description", "seo_analyzer"),
        }),
        ("Product Review Data (Optional)", {
            "classes": ("collapse",), # এটি ডিফল্টভাবে লুকানো থাকবে
            "fields": ("product_name", "product_price", "product_url", "rating_value"),
        }),
        ("Publishing Status", {
            "fields": ("status", "tags", "views_count"),
        }),
    )

    # ভিউ কাউন্ট এবং এসইও এনালাইজারকে শুধু দেখার জন্য (Read Only) রাখা হয়েছে
    readonly_fields = ['seo_analyzer', 'views_count']

    # --- ওয়ার্ডপ্রেস স্টাইল: সরাসরি ওয়েবসাইট থেকে পোস্ট দেখার বাটন ---
    def view_post_link(self, obj):
        # মডেলে get_absolute_url থাকলে এটি কাজ করবে
        return format_html(
            '<a href="{}" target="_blank" '
            'style="background-color: #007bff; color: white; padding: 5px 12px; '
            'border-radius: 4px; text-decoration: none; font-weight: bold; font-size: 12px;">'
            '👁️ Post</a>', 
            obj.get_absolute_url()
        )
    view_post_link.short_description = "Live Preview"

    # --- SEO Live Analyzer (HTMX ভিত্তিক) ---
    def seo_analyzer(self, obj):
        return mark_safe(
            '''
            <div id="seo-result-box" style="margin-bottom: 15px; min-height: 50px; background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #17a2b8; border-right: 1px solid #ddd; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">
                <span style="color: #666; font-style: italic;">
                    আর্টিকেলের SEO স্কোর দেখতে নিচের বাটনে ক্লিক করুন:
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
                // বাটন ক্লিক করলে এডিটরের ডাটা সিঙ্ক হবে
                document.getElementById('seo-check-btn').addEventListener('click', function() {
                    // CKEditor 5 বা CKEditor 4 সিঙ্ক
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

                // HTMX রিকোয়েস্ট পাঠানোর আগে ডাটা রিফ্রেশ করা
                document.body.addEventListener('htmx:configRequest', function(evt) {
                    if (typeof CKEDITOR !== 'undefined' && CKEDITOR.instances['id_post_details']) {
                        CKEDITOR.instances['id_post_details'].updateElement();
                    }
                });
            </script>
            '''
        )
    seo_analyzer.short_description = "SEO Live Analyzer"

    # --- Status Toggle Button (HTMX ভিত্তিক) ---
    def status_button(self, obj):
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
        'js/keyword_counter.js', # আপনার কাস্টম জাভাস্ক্রিপ্ট ফাইল
        )
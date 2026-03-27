from django.contrib import admin
from .models import EmailChangeRequest
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
    # list_display তে 'created_at' এর পরিবর্তে 'formatted_date' ব্যবহার করা হয়েছে
    list_display = ["title", "category", "status_button", "view_post_link", "formatted_date"]
    list_filter = ["status", "category", "author", "created_at"]
    search_fields = ["title", "focus_keyword", "category__category_title"]
    
    # টাইটেল লিখলে অটো স্ল্যাগ জেনারেট হবে (Wordpress এর মতো সুবিধা)
    prepopulated_fields = {"slug": ("title",)}
    
    # এডিট পেজে ফিল্ডগুলোকে সুন্দরভাবে সেকশন অনুযায়ী সাজানো (Fieldsets)
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

    # ভিউ কাউন্ট এবং এসইও এনালাইজারকে শুধু দেখার জন্য (Read Only) রাখা হয়েছে
    readonly_fields = ['seo_analyzer', 'views_count']

    # --- কাস্টম তারিখ ফরম্যাট (DD/MM/YYYY) ---
    def formatted_date(self, obj):
        if obj.created_at:
            # এখানে দিন/মাস/বছর এবং সময় (১২ ঘণ্টার ফরম্যাটে) সেট করা হয়েছে
            return obj.created_at.strftime("%d/%m/%Y, %I:%M %p")
        return "-"
    formatted_date.short_description = "Created at"
    formatted_date.admin_order_field = 'created_at'

    # --- ওয়ার্ডপ্রেস স্টাইল: সরাসরি ওয়েবসাইট থেকে পোস্ট দেখার বাটন ---
    def view_post_link(self, obj):
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
                document.getElementById('seo-check-btn').addEventListener('click', function() {
                    if (typeof CKEDITOR !== 'undefined') {
                        for (var instance in CKEDITOR.instances) {
                            CKEDITOR.instances[instance].updateElement();
                        }
                    }
                    if (typeof tinymce !== 'undefined') {
                        tinymce.triggerSave();
                    }
                });

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
        'js/keyword_counter.js', 
        )

@admin.register(EmailChangeRequest)
class EmailChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'new_email', 'is_approved', 'created_at']
    actions = ['approve_email_change']

    def approve_email_change(self, request, queryset):
        for req in queryset:
            if not req.is_approved:
                user = req.user
                user.email = req.new_email
                user.save()
                req.is_approved = True
                req.save()
        self.message_user(request, "Selected email changes have been approved and updated!")
    
    approve_email_change.short_description = "Approve selected email changes"
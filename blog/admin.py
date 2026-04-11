from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from .models import *
from .views import master_analytics_dashboard
from .admin_utils import seo_analyzer_html, get_link_stats # কাস্টম ইমপোর্ট

# ১. সাধারণ রেজিস্ট্রেশন
admin.site.register([Author, Category, Comment, Reply])

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "category", "status_button", "links_info", "view_post_link", "formatted_date"]
    list_filter = ["status", "category", "author", "created_at"]
    search_fields = ["title", "focus_keyword", "category__category_title"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ['seo_analyzer', 'views_count']
    
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

    # --- Methods ---
    def links_info(self, obj):
        internal, outbound = get_link_stats(obj.post_details)
        return format_html("In: {} | Out: {}", internal, outbound)
    links_info.short_description = "Links (Int|Ext)"

    def formatted_date(self, obj):
        return obj.created_at.strftime("%d/%m/%Y, %I:%M %p") if obj.created_at else "-"
    formatted_date.short_description = "Created"

    def view_post_link(self, obj):
        return format_html('<a href="{}" target="_blank" style="background:#007bff; color:white; padding:4px 8px; border-radius:4px; font-size:11px;">👁️ View</a>', obj.get_absolute_url())

    def seo_analyzer(self, obj):
        return seo_analyzer_html()

    def status_button(self, obj):
        if not obj.id: return "-"
        color = "#28a745" if obj.status == "published" else "#ffc107"
        return format_html('<button type="button" style="background:{}; color:white; border:none; padding:4px 8px; border-radius:4px; cursor:pointer;" hx-post="/toggle-status/{}/" hx-swap="outerHTML">{}</button>', color, obj.id, obj.status.title())

    class Media:
        js = ('https://unpkg.com/htmx.org@1.9.10', 'js/keyword_counter.js')

# --- অন্যান্য মডেল ---

@admin.register(EmailChangeRequest)
class EmailChangeRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'new_email', 'is_approved', 'created_at']
    actions = ['approve_email_change']

    def approve_email_change(self, request, queryset):
        for req in queryset.filter(is_approved=False):
            req.user.email = req.new_email
            req.user.save()
            req.is_approved = True
            req.save()
        self.message_user(request, "Approved and Updated!")

@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    # 'order' ফিল্ডটি list_display তে প্রথম আছে এবং list_editable এও আছে
    list_display = ('order', 'title', 'slug', 'is_active', 'updated_at')
    list_editable = ('order', 'is_active') 
    
    # এরর ফিক্স করতে এই লাইনটি অবশ্যই লাগবে:
    # এটি নিশ্চিত করে যে 'title' এ ক্লিক করলে এডিট পেজে যাবে, 'order' এ নয়।
    list_display_links = ('title',) 
    
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'subscribed_at')
    search_fields = ('email',)

# --- Custom Admin URLs ---
original_get_urls = admin.site.get_urls
def get_urls():
    custom_urls = [path('analytics-dashboard/', admin.site.admin_view(master_analytics_dashboard), name="full_analytics")]
    return custom_urls + original_get_urls()
admin.site.get_urls = get_urls
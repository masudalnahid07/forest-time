# admin_utils.py
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from bs4 import BeautifulSoup

def get_link_stats(content, domain="floorcrafted.com"):
    if not content:
        return 0, 0
    soup = BeautifulSoup(content, 'html.parser')
    links = soup.find_all('a', href=True)
    
    internal = sum(1 for link in links if link['href'].startswith('/') or domain in link['href'])
    outbound = sum(1 for link in links if link['href'].startswith('http') and domain not in link['href'])
    return internal, outbound

def seo_analyzer_html():
    return mark_safe('''
        <div id="seo-result-box" style="margin-bottom: 15px; min-height: 50px; background: #f8f9fa; padding: 15px; border-radius: 5px; border: 1px solid #ddd; border-left: 5px solid #17a2b8;">
            <span style="color: #666; font-style: italic;">আর্টিকেলের SEO স্কোর দেখতে নিচের বাটনে ক্লিক করুন:</span>
        </div>
        
        <button type="button" 
                id="seo-check-btn" 
                hx-post="/live-seo-checker/" 
                hx-include="closest form" 
                hx-target="#seo-result-box"
                hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
                style="background: #17a2b8; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-weight: bold;">
            🔍 Check SEO Match
        </button>

        <script>
            document.body.addEventListener('htmx:configRequest', (event) => {
                // CSRF Token নিশ্চিত করা
                event.detail.headers['X-CSRFToken'] = document.querySelector('[name=csrfmiddlewaretoken]').value;
                
                // এডিটর থেকে ডেটা সিঙ্ক করা (CKEditor 4/5 বা TinyMCE এর জন্য)
                if (typeof CKEDITOR !== 'undefined') {
                    for (var instance in CKEDITOR.instances) {
                        CKEDITOR.instances[instance].updateElement();
                    }
                }
                if (typeof tinymce !== 'undefined') {
                    tinymce.triggerSave();
                }
            });
        </script>
    ''')
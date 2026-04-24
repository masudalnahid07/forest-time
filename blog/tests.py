import requests
import os
import random
from dotenv import load_dotenv

# .env ফাইল থেকে API Key এবং অন্যান্য তথ্য লোড করা
load_dotenv()

# --- ১. কনফিগারেশন এবং কনস্ট্যান্টস ---
BASE_URL = "http://127.0.0.1:8000/api/v2"
API_KEY = os.getenv("NINJA_API_KEY")
HEADERS = {"X-API-KEY": API_KEY}

# --- ২. ডায়নামিক ভ্যালু (এগুলো আপনার লুপ বা ফাংশন থেকে আসবে) ---
# উদাহরণস্বরূপ আপনার ওয়ার্ডপ্রেস কোডের মতো ভেরিয়েবল রাখা হলো
keyword = "Best Smart Vacuum Cleaner 2026"
local_image_path = "vacuum.jpg"  # এই ফাইলটি স্ক্রিপ্টের ফোল্ডারে থাকতে হবে

# --- ৩. ডাটা জেনারেট করার ফাংশন (আপনার লজিক অনুযায়ী) ---
def generate_article_payload(keyword, uploaded_img_path):
    """
    এখানে আপনার ওয়ার্ডপ্রেসের মতো কন্টেন্ট জেনারেশন লজিক থাকবে।
    uploaded_img_path হলো সার্ভার থেকে পাওয়া ইমেজের পাথ।
    """
    title = f"{keyword}: The Ultimate Guide for Homeowners"
    content = f"""
    <h2>Introduction to {keyword}</h2>
    <p>This is a human-like SEO optimized content about {keyword}.</p>
    <p><i>Everything written here follows your WordPress logic.</i></p>
    """
    
    # এটি আপনার BlogPostIn Schema এর সাথে মিল রেখে তৈরি
    data = {
        "title": title,
        "slug": keyword.lower().replace(" ", "-"),
        "feature_img_path": uploaded_img_path, # <--- সার্ভার থেকে পাওয়া পাথ এখানে বসবে
        "post_details": content,
        "post_type": "info",
        "category_id": 1,  # আপনার ডাটাবেসের ক্যাটাগরি আইডি
        "author_id": 1,
        "status": "published",
        "focus_keyword": keyword,
        "meta_description": f"Read our expert review on {keyword}."
    }
    return data

# --- ৪. মূল আপলোড লজিক (আপনার ওয়ার্ডপ্রেস লজিক স্টাইলে) ---
def run_uploader():
    if not os.path.exists(local_image_path):
        print(f"Error: Image file '{local_image_path}' not found!")
        return

    try:
        # ধাপ ১: ইমেজ আপলোড করে পাথ নেওয়া (WordPress: upload_img_get_id স্টাইল)
        print(f"Uploading image: {local_image_path}...")
        with open(local_image_path, "rb") as img_file:
            files = {"file": img_file}
            img_res = requests.post(f"{BASE_URL}/upload-media", files=files, headers=HEADERS)
            img_res.raise_for_status() # এরর থাকলে কোড এখানেই থামবে
            
            server_img_path = img_res.json().get("image_path")
            print(f"Image uploaded successfully! Path: {server_img_path}")

        # ধাপ ২: ডাটা ডিকশনারি তৈরি (ইমেজ পাথসহ)
        article_payload = generate_article_payload(keyword, server_img_path)

        # ধাপ ৩: মেইন পোস্ট তৈরি করা
        print(f"Creating post: {article_payload['title']}...")
        post_res = requests.post(f"{BASE_URL}/create-posts", json=article_payload, headers=HEADERS)
        
        if post_res.status_code == 200:
            result = post_res.json()
            print(f"✅ Success! Post Created. ID: {result.get('id')}")
        else:
            print(f"❌ Failed to create post: {post_res.text}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_uploader()
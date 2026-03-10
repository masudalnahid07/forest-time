from .models import Category

def category_context(request):
    # এটি আপনার ডাটাবেস থেকে সব ক্যাটাগরি নিয়ে আসবে
    return {
        'all_categories': Category.objects.all()
    }
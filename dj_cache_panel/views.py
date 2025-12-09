from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.conf import settings


@staff_member_required
def index(request):
    context = {
        "caches": settings.CACHES,
        "title": "DJ Cache Panel - Instances",
    }
    return render(request, "admin/dj_cache_panel/index.html", context)

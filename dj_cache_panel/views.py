from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.conf import settings
from django.contrib import admin

from dj_cache_panel.cache_panel import get_cache_panel


def _get_page_range(current_page, total_pages, window=2):
    """
    Generate a page range for pagination display.
    Shows pages around current page with ellipsis for gaps.
    """
    if total_pages <= 7:
        return list(range(1, total_pages + 1))

    pages = []

    # Always show first page
    pages.append(1)

    # Calculate range around current page
    start = max(2, current_page - window)
    end = min(total_pages - 1, current_page + window)

    # Add ellipsis if there's a gap after first page
    if start > 2:
        pages.append("...")

    # Add pages around current
    for p in range(start, end + 1):
        pages.append(p)

    # Add ellipsis if there's a gap before last page
    if end < total_pages - 1:
        pages.append("...")

    # Always show last page
    if total_pages > 1:
        pages.append(total_pages)

    return pages


@staff_member_required
def index(request):
    """
    Display all configured cache instances with their panel abilities.
    """
    # Build cache info with panel abilities
    caches_info = []
    for cache_name, cache_config in settings.CACHES.items():
        try:
            cache_panel = get_cache_panel(cache_name)
            cache_info = {
                "name": cache_name,
                "config": cache_config,
                "backend": cache_config.get("BACKEND", "Unknown"),
                "backend_short": cache_config.get("BACKEND", "").split(".")[-1],
                "abilities": cache_panel.ABILITIES,
            }
            caches_info.append(cache_info)
        except Exception as e:
            # If we can't get panel info, still show the cache
            cache_info = {
                "name": cache_name,
                "config": cache_config,
                "backend": cache_config.get("BACKEND", "Unknown"),
                "backend_short": cache_config.get("BACKEND", "").split(".")[-1],
                "abilities": {},
                "error": str(e),
            }
            caches_info.append(cache_info)

    context = admin.site.each_context(request)

    context.update(
        {
            "caches_info": caches_info,
            "title": "DJ Cache Panel - Instances",
        }
    )
    return render(request, "admin/dj_cache_panel/index.html", context)


@staff_member_required
def key_search(request, cache_name: str):
    """
    View for searching/browsing cache keys.

    If the cache backend supports 'query', we can list all keys.
    If not, we show a message but still allow exact key lookups.
    """
    cache_panel = get_cache_panel(cache_name)
    cache_config = settings.CACHES.get(cache_name, {})

    context = admin.site.each_context(request)

    context.update(
        {
            "cache_name": cache_name,
            "cache_config": cache_config,
            "title": f"{cache_name} - Search Keys",
            "query_supported": cache_panel.is_feature_supported("query"),
            "get_key_supported": cache_panel.is_feature_supported("get_key"),
            "abilities": cache_panel.abilities,
        }
    )

    # Get search parameters
    search_query = request.GET.get("q", "").strip()
    per_page = int(request.GET.get("per_page", 25))
    page = int(request.GET.get("page", 1))

    context["search_query"] = search_query
    context["per_page"] = per_page
    context["current_page"] = page

    # Handle exact key lookup (always allowed if get_key is supported)
    if search_query and cache_panel.is_feature_supported("get_key"):
        # Check if this is an exact key lookup (no wildcards)
        if "*" not in search_query and "?" not in search_query:
            key_result = cache_panel.get_key(search_query)
            if key_result.get("exists"):
                context["exact_match"] = key_result
                context["keys_data"] = [
                    {
                        "key": key_result["key"],
                        "value": key_result["value"],
                        "type": key_result.get("type", "unknown"),
                    }
                ]
                context["total_keys"] = 1
                return render(request, "admin/dj_cache_panel/key_search.html", context)

    # Handle pattern search (only if query is supported)
    if cache_panel.is_feature_supported("query"):
        pattern = search_query if search_query else "*"
        try:
            query_result = cache_panel.query(
                instance_alias=cache_name,
                pattern=pattern,
                page=page,
                per_page=per_page,
            )

            keys = query_result["keys"]
            total_count = query_result["total_count"]

            # Build keys_data with basic info
            keys_data = []
            for key in keys:
                key_info = cache_panel.get_key(key)
                keys_data.append(
                    {
                        "key": key,
                        "value": key_info.get("value"),
                        "type": key_info.get("type", "unknown"),
                    }
                )

            context["keys_data"] = keys_data
            context["total_keys"] = total_count

            # Pagination info
            total_pages = (total_count + per_page - 1) // per_page
            context["total_pages"] = total_pages
            context["has_previous"] = page > 1
            context["has_next"] = page < total_pages
            context["previous_page"] = page - 1
            context["next_page"] = page + 1

            # Generate page range for pagination display
            context["page_range"] = _get_page_range(page, total_pages)

            # Calculate start/end indices for display
            context["start_index"] = (page - 1) * per_page + 1
            context["end_index"] = min(page * per_page, total_count)

        except Exception as e:
            context["error_message"] = str(e)

    return render(request, "admin/dj_cache_panel/key_search.html", context)

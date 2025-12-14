import json
from urllib.parse import unquote
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import admin, messages
from django.urls import reverse

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
                "backend_short": cache_config.get("BACKEND", ""),
                "abilities": cache_panel.abilities,
            }
            caches_info.append(cache_info)
        except Exception as e:
            # If we can't get panel info, still show the cache
            cache_info = {
                "name": cache_name,
                "config": cache_config,
                "backend": cache_config.get("BACKEND", "Unknown"),
                "backend_short": cache_config.get("BACKEND", ""),
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

    # Handle POST requests (flush cache)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "flush" and cache_panel.is_feature_supported("flush_cache"):
            try:
                result = cache_panel.flush_cache()
                messages.success(request, result["message"])
                # Redirect to refresh the page
                return redirect(reverse("dj_cache_panel:key_search", args=[cache_name]))
            except Exception as e:
                messages.error(request, f"Error flushing cache: {str(e)}")
                # Still redirect to show the error message
                return redirect(reverse("dj_cache_panel:key_search", args=[cache_name]))

    context = admin.site.each_context(request)

    context.update(
        {
            "cache_name": cache_name,
            "cache_config": cache_config,
            "query_supported": cache_panel.is_feature_supported("query"),
            "get_key_supported": cache_panel.is_feature_supported("get_key"),
            "flush_supported": cache_panel.is_feature_supported("flush_cache"),
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
                key_data = {
                    "key": key_result["key"],
                }
                context["keys_data"] = [key_data]
                context["total_keys"] = 1
                return render(request, "admin/dj_cache_panel/key_search.html", context)
            else:
                # Key doesn't exist - show a message
                messages.error(request, f"Key '{search_query}' not found in cache.")
                context["keys_data"] = []
                context["total_keys"] = 0
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
            error = query_result.get("error")

            # If there's an error, show it
            if error:
                context["error"] = error

            # Build keys_data with basic info (no value fetching)
            keys_data = []
            for key_item in keys:
                # Handle both dict format (from Redis) and string format (from other backends)
                if isinstance(key_item, dict):
                    user_key = key_item["key"]
                    redis_key = key_item.get("redis_key")
                else:
                    user_key = key_item
                    redis_key = None

                key_data = {
                    "key": user_key,
                }
                # Add redis_key if available (for Redis backends)
                if redis_key:
                    key_data["redis_key"] = redis_key
                keys_data.append(key_data)

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
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"Error querying cache '{cache_name}': {str(e)}", exc_info=True
            )
            context["error_message"] = str(e)
            # Also check if there's an error in the query result
            if hasattr(e, "args") and e.args:
                context["error_message"] = f"{str(e)}: {e.args[0] if e.args else ''}"

    return render(request, "admin/dj_cache_panel/key_search.html", context)


@staff_member_required
def key_detail(request, cache_name: str, key: str):
    """
    View for displaying the details of a specific cache key.
    Handles both GET (display) and POST (update/delete) requests.
    """

    # Decode the key in case it was URL encoded
    key = unquote(key)

    cache_panel = get_cache_panel(cache_name)

    # Handle POST requests (update or delete)
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "delete" and cache_panel.is_feature_supported("delete_key"):
            try:
                result = cache_panel.delete_key(key)
                messages.success(request, "Key deleted successfully.")
                # Redirect back to key search
                return redirect(reverse("dj_cache_panel:key_search", args=[cache_name]))
            except Exception as e:
                messages.error(request, f"Error deleting key: {str(e)}")

        elif action == "update" and cache_panel.is_feature_supported("edit_key"):
            try:
                new_value = request.POST.get("value", "")
                # Try to parse as JSON if it looks like JSON
                try:
                    new_value = json.loads(new_value)
                except (json.JSONDecodeError, ValueError):
                    # Keep as string if not valid JSON
                    pass

                # Get timeout value (optional)
                timeout_str = request.POST.get("timeout", "").strip()
                timeout = None
                timeout_error = False
                if timeout_str:
                    try:
                        timeout = float(timeout_str)
                        if timeout < 0:
                            raise ValueError("Timeout must be non-negative")
                    except ValueError as e:
                        messages.error(request, f"Invalid timeout value: {str(e)}")
                        timeout_error = True
                        # Continue to display the form with error - don't redirect

                # Only proceed if there was no timeout error
                if not timeout_error:
                    result = cache_panel.edit_key(key, new_value, timeout=timeout)
                    messages.success(request, result["message"])
                    # Redirect to refresh the page
                    return redirect(
                        reverse("dj_cache_panel:key_detail", args=[cache_name, key])
                    )
            except Exception as e:
                messages.error(request, f"Error updating key: {str(e)}")

    # GET request - display the key
    key_result = cache_panel.get_key(key)

    # Format value for display in input field
    value_display = key_result.get("value")
    if value_display is not None:
        if isinstance(value_display, (dict, list)):
            value_display = json.dumps(value_display, indent=2)
        else:
            value_display = str(value_display)
    else:
        value_display = ""

    cache_config = settings.CACHES.get(cache_name, {})
    key_exists = key_result.get("exists", False)

    context = admin.site.each_context(request)
    context.update(
        {
            "cache_name": cache_name,
            "cache_config": cache_config,
            "key": key,
            "key_value": key_result,
            "key_exists": key_exists,
            "value_display": value_display,
            "query_supported": cache_panel.is_feature_supported("query"),
            "get_key_supported": cache_panel.is_feature_supported("get_key"),
            "delete_supported": cache_panel.is_feature_supported("delete_key")
            and key_exists,
            "edit_supported": cache_panel.is_feature_supported("edit_key")
            and key_exists,
        }
    )
    return render(request, "admin/dj_cache_panel/key_detail.html", context)


@staff_member_required
def key_add(request, cache_name: str):
    """
    View for adding a new cache key.
    Handles both GET (display form) and POST (create key) requests.
    """

    # Decode the cache name in case it was URL encoded
    cache_name = unquote(cache_name)

    cache_panel = get_cache_panel(cache_name)
    cache_config = settings.CACHES.get(cache_name, {})

    # Handle POST requests (create key)
    if request.method == "POST":
        if cache_panel.is_feature_supported("edit_key"):
            try:
                key_name = request.POST.get("key", "").strip()
                value = request.POST.get("value", "").strip()

                if not key_name:
                    messages.error(request, "Key name is required.")
                else:
                    # Try to parse as JSON if it looks like JSON
                    try:
                        parsed_value = json.loads(value)
                    except (json.JSONDecodeError, ValueError):
                        # Keep as string if not valid JSON
                        parsed_value = value

                    # Get timeout value (optional)
                    timeout_str = request.POST.get("timeout", "").strip()
                    timeout = None
                    timeout_error = False
                    if timeout_str:
                        try:
                            timeout = float(timeout_str)
                            if timeout < 0:
                                raise ValueError("Timeout must be non-negative")
                        except ValueError as e:
                            messages.error(request, f"Invalid timeout value: {str(e)}")
                            timeout_error = True
                            # Continue to display the form with error - don't redirect

                    # Only proceed if there was no timeout error
                    if not timeout_error:
                        # Use edit_key to create the key (it will create if it doesn't exist)
                        cache_panel.edit_key(key_name, parsed_value, timeout=timeout)
                        messages.success(
                            request, f"Key '{key_name}' created successfully."
                        )
                        # Redirect back to key search
                        return redirect(
                            reverse("dj_cache_panel:key_search", args=[cache_name])
                        )
            except Exception as e:
                messages.error(request, f"Error creating key: {str(e)}")
        else:
            messages.error(
                request, "Adding keys is not supported for this cache backend."
            )

    # GET request - display the form
    context = admin.site.each_context(request)
    context.update(
        {
            "cache_name": cache_name,
            "cache_config": cache_config,
            "edit_supported": cache_panel.is_feature_supported("edit_key"),
        }
    )
    return render(request, "admin/dj_cache_panel/key_add.html", context)

class CachePanel:
    id = "dj_cache_panel"
    name = "Cache Panel"
    description = "Inspect and manage Django cache backends"
    icon = "layers"

    def get_url_name(self):
        return "index"

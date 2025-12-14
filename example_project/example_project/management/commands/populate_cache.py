from django.core.management.base import BaseCommand
from django.core.cache import caches
from django.conf import settings


class Command(BaseCommand):
    help = """
    Populate the cache with test data.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--cache_name",
            type=str,
            help="The name of the cache to populate",
            required=False,
            default="default",
        )
        parser.add_argument(
            "--all_caches",
            action="store_true",
            help="Populate all caches",
            required=False,
        )
        parser.add_argument(
            "--num_keys", type=int, default=100, help="The number of keys to populate"
        )

    def handle(self, *args, **options):
        cache_names = options.get("cache_name")
        num_keys = options.get("num_keys")

        if options.get("all_caches"):
            cache_names = settings.CACHES.keys()
        else:
            cache_names = [cache_names]

        for cache_name in cache_names:
            try:
                for i in range(num_keys):
                    key = f"test_key_{i}"
                    value = f"test_value_{i}"
                    caches[cache_name].set(key, value)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully populated {num_keys} keys to {cache_name}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to populate {cache_name}: {e}")
                )

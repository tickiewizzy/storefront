from django.contrib.sitemaps import Sitemap
from blog.models import Entry

class EntrySitemap(Sitemap):
    changefreq = 'never'
    priority = 0.1

    def items(self):
        return Entry.objects.published()

    def lastmod(self, obj):
        return obj.date_published
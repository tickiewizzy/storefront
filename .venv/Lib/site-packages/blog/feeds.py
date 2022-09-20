from django.contrib.sites.models import Site
from django.contrib.syndication.feeds import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from blog.models import Entry

class EntryLatest(Feed):
    feed_type = Rss201rev2Feed
    title_template = None
    description_template = None

    title = 'Blog'
    link =  '/blog/'
    language = 'en'
    description = ''

    def feed_copyright(self):
        site = Site.objects.get_current()
        return u'(c) %s' % site.name

    def items(self):
        return Entry.objects.published()

    def item_pubdate(self, item):
        return item.date_published

    def item_description(self, item):
        return item.content
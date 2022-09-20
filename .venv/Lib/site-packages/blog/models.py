from datetime import datetime
from autoslug import AutoSlugField
from django.db import models
from taggit.managers import TaggableManager

class EntryManager(models.Manager):
    def drafts(self):
        """
        Returns a queryset with drafts
        """
        return self.get_query_set().filter(status=0)

    def published(self):
        """
        Returns a queryset with published entries
        """
        return self.get_query_set().filter(status=1, date_published__lte=datetime.now())

    def recent(self, limit=2):
        """
        Returns a queryset with recent entries
        """
        return self.published()[:limit]

STATUS_CHOICES = (
    (0, 'Draft'),
    (1, 'Published'),
)

class Entry(models.Model):
    headline = models.CharField(max_length=100)
    slug = AutoSlugField(max_length=100, populate_from='headline', unique=True)
    intro = models.CharField(max_length=100, blank=True, help_text='A short introductory text')
    content = models.TextField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    author = models.ForeignKey('auth.User', related_name='entries')

    date_created = models.DateTimeField(auto_now_add=True, blank=True, null=True, editable=False)
    date_changed = models.DateTimeField(auto_now=True, blank=True, null=True, editable=False)
    date_published = models.DateTimeField('Publication date', default=datetime.now,
                                          help_text='Use future date and time for delayed publications')

    objects = EntryManager()
    tags = TaggableManager()

    class Meta:
        ordering = ('-date_published',)
        verbose_name_plural = 'Entries'

    def __unicode__(self):
        return self.headline

    @models.permalink
    def get_absolute_url(self):
        return ('entry_date_detail', (), {
            'year': self.date_published.year,
            'month': self.date_published.month,
            'day': self.date_published.day,
            'slug': self.slug
        })

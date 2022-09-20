from django.conf.urls.defaults import *
from blog.views import EntryArchiveIndexView, EntryYearArchiveView, \
    EntryMonthArchiveView, EntryDayArchiveView, EntryDateDetailView

urlpatterns = patterns('',
    url(r'^$', EntryArchiveIndexView.as_view(), name='entry_archive_index'),
    url(r'^(?P<year>\d+)/$', EntryYearArchiveView.as_view(),
        name='entry_year_archive'),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/$', EntryMonthArchiveView.as_view(),
        name='entry_month_archive'),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', EntryDayArchiveView.as_view(),
        name='entry_day_archive'),
    url(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[\w-]+)/$', EntryDateDetailView.as_view(),
        name='entry_date_detail'),
)
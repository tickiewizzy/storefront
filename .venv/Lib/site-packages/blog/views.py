from django.views.generic import DateDetailView, YearArchiveView, MonthArchiveView, \
    DayArchiveView, ArchiveIndexView
from blog.models import Entry

class EntryArchiveIndexView(ArchiveIndexView):
    date_field = 'date_published'
    model = Entry
    queryset = Entry.objects.published()

class EntryYearArchiveView(YearArchiveView):
    date_field = 'date_published'
    model = Entry
    queryset = Entry.objects.published()

class EntryMonthArchiveView(MonthArchiveView):
    date_field = 'date_published'
    model = Entry
    month_format = '%m'
    queryset = Entry.objects.published()

class EntryDayArchiveView(DayArchiveView):
    date_field = 'date_published'
    model = Entry
    month_format = '%m'
    queryset = Entry.objects.published()

class EntryDateDetailView(DateDetailView):
    date_field = 'date_published'
    model = Entry
    month_format = '%m'
    queryset = Entry.objects.published()
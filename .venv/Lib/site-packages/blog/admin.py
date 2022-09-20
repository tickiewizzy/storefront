from django.contrib import admin
from blog.models import Entry

class EntryAdmin(admin.ModelAdmin):
    actions = None
    list_display = ('headline', 'date_published', 'status')
    list_display_links = ('headline',)
    list_filter = ('status',)
    ordering = ('-date_published',)
    search_fields = ('headline',)

    class Media:
        js = (
            'scripts/jquery/jquery-1.4.2.min.js',
            'tiny_mce/tiny_mce.js',
            'tiny_mce/tinymce_setup.js',
            )

admin.site.register(Entry, EntryAdmin)
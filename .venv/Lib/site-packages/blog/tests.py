from datetime import date, datetime, timedelta
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from blog.models import Entry

class BlogTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user('test', 'test@test.com', 'test')

    def test_entry_archive_index(self):
        # No news - 404
        response = self.client.get(reverse('entry_archive_index'))
        self.assertEqual(response.status_code, 404)

        # Create a blog entry
        e = Entry.objects.create(headline='Test 1', content='Testing', status=1,
                                 date_published=datetime.now() - timedelta(seconds=10),
                                 author=self.user)
        response = self.client.get(reverse('entry_archive_index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 1)
        assert e in response.context['object_list']

    def test_entry_year_archive(self):
        # No blog entries - 404
        response = self.client.get(reverse('entry_year_archive', kwargs={'year': datetime.now().year}))
        self.assertEqual(response.status_code, 404)

        # Create a blog entry
        now = datetime.now() - timedelta(seconds=10)
        Entry.objects.create(headline='Test 1', content='Test', status=1, date_published=now, author=self.user)
        response = self.client.get(reverse('entry_year_archive', kwargs={'year': now.year}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['year'], str(now.year))
        self.assertEqual(len(response.context['date_list']), 1)
        self.assertEqual(response.context['date_list'][0], datetime(now.year, now.month, 1))

    def test_entry_month_archive(self):
        # No blog entries - 404
        now = datetime.now() - timedelta(seconds=10)
        response = self.client.get(reverse('entry_month_archive',
                                           kwargs={'year': now.year, 'month': now.month}))
        self.assertEqual(response.status_code, 404)

        # Create a blog entry
        e = Entry.objects.create(headline='Test 1', content='Test', status=1, date_published=now, author=self.user)
        response = self.client.get(reverse('entry_month_archive',
                                           kwargs={'year': now.year, 'month': now.month}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['month'], date(now.year, now.month, 1))
        self.assertEqual(len(response.context['date_list']), 1)
        self.assertEqual(response.context['date_list'][0], datetime(now.year, now.month, now.day))

    def test_entry_day_archive(self):
        # No blog entries - 404
        now = datetime.now() - timedelta(seconds=10)
        response = self.client.get(reverse('entry_day_archive',
                                           kwargs={
                                               'year': now.year,
                                               'month': now.month,
                                               'day': now.day
                                           }))
        self.assertEqual(response.status_code, 404)

        # Create a blog entry
        e = Entry.objects.create(headline='Test 1', content='Test', status=1, date_published=now, author=self.user)
        response = self.client.get(reverse('entry_day_archive',
                                           kwargs={
                                               'year': now.year,
                                               'month': now.month,
                                               'day': now.day
                                           }))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['day'], date(now.year, now.month, now.day))
        self.assertEqual(len(response.context['object_list']), 1)
        self.assertEqual(response.context['object_list'][0], e)

    def test_entry_date_detail(self):
        # Blog entry not published - 404
        now = datetime.now() - timedelta(seconds=10)
        e = Entry.objects.create(headline='Test 1', content='Test', status=0, date_published=now, author=self.user)
        response = self.client.get(e.get_absolute_url())
        self.assertEqual(response.status_code, 404)

        # Publish this blog entry
        e.status = 1
        e.save()
        response = self.client.get(e.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'], e)

from django.test import SimpleTestCase
from django.urls import reverse, resolve
from crawler.views import home, crawler, crawler_rpf, result, rfp_result, update_result


class TestUrls(SimpleTestCase):

    def test_home_url_is_resolved(self):
        """

        Returns true when the url 'home' triggers the home API

       """

        url = reverse('home')
        self.assertEquals(resolve(url).func, home)

    def test_crawler_url_is_resolved(self):
        """

        Returns true when the url 'crawler' triggers the crawler API

       """

        url = reverse('crawler', args=['some-string'])
        self.assertEquals(resolve(url).func, crawler)

    def test_crawler_rfp_url_is_resolved(self):
        """

        Returns true when the url 'crawler_rfp' triggers the crawler_rfp API

       """
        url = reverse('crawler_rfp')
        self.assertEquals(resolve(url).func, crawler_rpf)

    def test_result_url_is_resolved(self):
        """

        Returns true when the url 'result' triggers the result API

       """

        url = reverse('result', args=['some-string'])
        self.assertEquals(resolve(url).func, result)

    def test_rfp_results_url_is_resolved(self):
        """

        Returns true when the url 'rfp_result' triggers the rfp_result API

       """

        url = reverse('rfp_result')
        self.assertEquals(resolve(url).func, rfp_result)

    def test_update_result_url_is_resolved(self):
        """

        Returns true when the url 'update_result' triggers the update_result API

       """

        url = reverse('update_result', args=['some-string'])
        self.assertEquals(resolve(url).func, update_result)
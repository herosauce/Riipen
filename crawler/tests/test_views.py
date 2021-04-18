from django.urls import reverse
from django.test import TestCase, Client
from crawler.models import RFP, Profile
import json


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()
        self.home_url = reverse('home')
        self.crawler_url = reverse('crawler', args=['epic radiant'])
        self.crawler_rfp_url = reverse('crawler_rfp')
        self.result_url = reverse('result', args=['epic radiant'])
        self.rfp_result_url = reverse('rfp_result')
        self.update_result_url = reverse('update_result', args=['epic radiant'])

    def test_home_GET(self):
        """

        Checks the status code when a GET request is made to the home API. And also checks the rendered template
        when the API is triggered.

       """

        response = self.client.get(self.home_url)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_result_GET(self):
        """

        Checks the status code when a GET request is made to the result API. And also checks the rendered template
        when the API is triggered.

       """

        response = self.client.get(self.result_url)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_rfp_result_GET(self):
        """

        Checks the status code when a GET request is made to the rfp_result API. And also checks the rendered template
        when the API is triggered.

       """

        response = self.client.get(self.rfp_result_url)

        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'rfp_data.html')

    def test_update_result_GET(self):
        """

        Checks the status code when a GET request is made to the update_result API.

       """

        response = self.client.get(self.update_result_url)

        self.assertEquals(response.status_code, 200)

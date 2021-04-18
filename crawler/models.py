# Create your models here.

from django.db import models


class Profile(models.Model):
    """
    Database model for User Profile

    """
    name = models.TextField(max_length=500, blank=True)
    linkedin_url = models.URLField(max_length=1500, blank=True)
    certifications = models.TextField(blank=True)
    current_job = models.TextField(max_length=500, blank=True)
    companies = models.TextField(blank=True)
    is_updated = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class RFP(models.Model):
    """
    Database model for RFPs to have contract title, url, number, and description
    """
    title = models.TextField(max_length=500, blank=True)
    url = models.URLField(max_length=1500, blank=True)
    contract_number = models.TextField(blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title

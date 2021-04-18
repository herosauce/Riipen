from django.contrib import admin
from django.urls import path

from crawler import views

urlpatterns = [
    path('', views.home, name='home'),
    path('crawl/<str:query>', views.crawler, name='crawler'),
    path('crawl_rfp/', views.crawler_rpf, name='crawler_rfp'),
    path('result/<str:query>', views.result, name='result'),
    path('rfp_result/', views.rfp_result, name='rfp_result'),
    path('update/<str:query>', views.update_result, name='update_result'),
]





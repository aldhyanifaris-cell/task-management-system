"""
Tasks App URLs
==============
URL patterns for Task and Category API endpoints.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register ViewSets
router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'categories', views.CategoryViewSet, basename='category')

app_name = 'tasks'

urlpatterns = [
    path('', include(router.urls)),
]

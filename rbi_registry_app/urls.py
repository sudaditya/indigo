"""
URL routes for RBI Registry endpoints.

All routes are prefixed with /api/rbi/ (see indigo/urls.py where
this module is included).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# DRF's DefaultRouter auto-generates list + detail URLs for each viewset.
router = DefaultRouter()
router.register(r'units', views.WorkingUnitViewSet, basename='workingunit')
router.register(r'mds', views.MDOwnershipViewSet, basename='mdownership')
router.register(r'drafts', views.DraftAmendmentViewSet, basename='draftamendment')

urlpatterns = [
    # ViewSets registered above
    path('', include(router.urls)),
    # Custom APIView (not a viewset — needs its own path)
    path('conflicts/', views.ConflictsView.as_view(), name='conflicts'),
    path('personas/', views.ViewablePersonasView.as_view(), name='personas'),  # ← NEW
]
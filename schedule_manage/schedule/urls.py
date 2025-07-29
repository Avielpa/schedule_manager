from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet, UnitViewSet, ImportBatchViewSet,
    SoldierViewSet, SoldierConstraintViewSet, SchedulingRunViewSet,
    AssignmentViewSet, EventViewSet
)

router = DefaultRouter()
# Hierarchical structure endpoints
router.register(r'organizations', OrganizationViewSet)
router.register(r'units', UnitViewSet)
router.register(r'import-batches', ImportBatchViewSet)

# Core functionality endpoints
router.register(r'soldiers', SoldierViewSet)
router.register(r'soldier-constraints', SoldierConstraintViewSet)
router.register(r'scheduling-runs', SchedulingRunViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]




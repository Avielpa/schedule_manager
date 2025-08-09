from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EventViewSet, SoldierViewSet, SoldierConstraintViewSet, 
    SchedulingRunViewSet, AssignmentViewSet
)

router = DefaultRouter()

# Simplified endpoints for Event -> Schedule -> Soldiers flow
router.register(r'events', EventViewSet)
router.register(r'soldiers', SoldierViewSet)
router.register(r'soldier-constraints', SoldierConstraintViewSet)
router.register(r'scheduling-runs', SchedulingRunViewSet)
router.register(r'assignments', AssignmentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]




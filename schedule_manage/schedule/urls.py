from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssignmentViewSet, SoldierViewSet, SchedulingRunViewSet,EventViewSet

router = DefaultRouter()
router.register(r'soldiers', SoldierViewSet)
router.register(r'scheduling-runs', SchedulingRunViewSet)
router.register(r'assignments', AssignmentViewSet)
router.register(r'events', EventViewSet)

urlpatterns = [
    path('', include(router.urls)),
]




from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"users", views.UserViewSet)

urlpatterns = [
    path('', views.api_root),
    path('images/', views.ImageList.as_view(), name="image-list"),
    path('images/<str:pk>', views.ImageDetails.as_view(), name="imageproduct-detail"),
    path('images/<str:pk>/link', views.LinkView.as_view(), name="image-link"),
    path('images/<str:pk>/get-temporary', views.ExpiringLinkView.as_view(), name="image-expiring-link"),
    path('temp/', views.temporary_link_view, name="temporary-link"),
    path('', include(router.urls))
]
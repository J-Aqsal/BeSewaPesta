from django.urls import path


from .views import UpSellAPIView, CrossSellAPIView


urlpatterns = [
    path("up-sell/", UpSellAPIView.as_view()),
    path("cross-sell/", CrossSellAPIView.as_view()),
]
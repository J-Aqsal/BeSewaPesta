from django.urls import path


from .views import UpSellAPIView, CrossSellAPIView


urlpatterns = [
    path("upsell/", UpSellAPIView.as_view()),
    path("crosssell/", CrossSellAPIView.as_view()),
]
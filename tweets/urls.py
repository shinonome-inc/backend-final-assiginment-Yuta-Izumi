from django.urls import path

from . import views

app_name = "tweets"
urlpatterns = [
    path("create/", views.TweetCreateView.as_view(), name="create"),
    path("<int:pk>/", views.TweetDetailView.as_view(), name="detail"),
    path("<int:pk>/delete/", views.TweetDeleteView.as_view(), name="delete"),
    path('<int:pk>/like/', views.like_view, name='like'),
    path('<int:pk>/unlike/', views.unlike_view, name='unlike'),
]

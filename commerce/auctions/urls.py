from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create/", views.create_listing, name="create_listing"),
    path("listing/<int:listing_id>/", views.listing_detail, name="listing_detail"),
    path("my_listings/", views.my_listings, name="my_listings"),
    path("my_bids/", views.my_bids, name="my_bids"),
    path('watchlist/', views.view_watchlist, name='watchlist'),
]

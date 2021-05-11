from django.conf.urls import url
from django.contrib.auth.views import LoginView, LogoutView

from apps.registration.views import *

urlpatterns = [
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),
    url(r'^register$', Register.as_view(), name='register'),
]

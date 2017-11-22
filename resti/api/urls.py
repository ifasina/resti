from django.conf.urls import url

from .views import CommandView

urlpatterns = [
	url(r'^cmd', CommandView.as_view(), name="cmd")
]
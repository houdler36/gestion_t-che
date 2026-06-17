from django.urls import path
from . import views

app_name = 'tracking'

urlpatterns = [
    path('log/create/', views.DailyLogCreateView.as_view(), name='log_create'),
    path('logs/', views.DailyLogListView.as_view(), name='log_list'),
]


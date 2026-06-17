from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportDashboardView.as_view(), name='report_dashboard'),
    path('project/<int:pk>/', views.ProjectReportView.as_view(), name='project_report'),
    path('user/<int:pk>/', views.UserReportView.as_view(), name='user_report'),
    path('export/project/<int:pk>/', views.export_project_report, name='export_project_report'),
]


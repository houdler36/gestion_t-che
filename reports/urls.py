from django.urls import path
from . import views
from .monthly_views import MonthlyReportDashboardView, export_monthly_report_csv

app_name = 'reports'

urlpatterns = [
    path('', views.ReportDashboardView.as_view(), name='report_dashboard'),
    path('monthly/', MonthlyReportDashboardView.as_view(), name='monthly_report_dashboard'),
    path('monthly/export/', export_monthly_report_csv, name='export_monthly_report_csv'),

    path('project/<int:pk>/', views.ProjectReportView.as_view(), name='project_report'),
    path('user/<int:pk>/', views.UserReportView.as_view(), name='user_report'),
    path('export/project/<int:pk>/', views.export_project_report, name='export_project_report'),
]




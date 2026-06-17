from django.urls import path

from projects import views

app_name = 'projects'

urlpatterns = [
    # Vues utilisateur (existantes)
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

    # ===== Vues admin custom =====
    path('admin/', views.AdminProjectListView.as_view(), name='admin_project_list'),
    path('admin/create/', views.AdminProjectCreateView.as_view(), name='admin_project_create'),
    path(
        'admin/<int:pk>/',
        views.AdminProjectDetailView.as_view(),
        name='admin_project_detail',
    ),
    path('admin/<int:pk>/update/', views.AdminProjectUpdateView.as_view(), name='admin_project_update'),
    path('admin/<int:pk>/delete/', views.AdminProjectDeleteView.as_view(), name='admin_project_delete'),

    path(
        'admin/<int:project_pk>/activity/create/',
        views.AdminActivityCreateView.as_view(),
        name='admin_activity_create',
    ),
    path(
        'admin/activity/<int:pk>/update/',
        views.AdminActivityUpdateView.as_view(),
        name='admin_activity_update',
    ),
    path(
        'admin/activity/<int:pk>/delete/',
        views.AdminActivityDeleteView.as_view(),
        name='admin_activity_delete',
    ),

    path(
        'admin/activity/<int:activity_pk>/subactivity/create/',
        views.AdminSubActivityCreateView.as_view(),
        name='admin_subactivity_create',
    ),
    path(
        'admin/subactivity/<int:pk>/update/',
        views.AdminSubActivityUpdateView.as_view(),
        name='admin_subactivity_update',
    ),
    path(
        'admin/subactivity/<int:pk>/delete/',
        views.AdminSubActivityDeleteView.as_view(),
        name='admin_subactivity_delete',
    ),
]


from django.contrib import admin
from .models import Project, ProjectMembership, Activity, SubActivity


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_date', 'end_date', 'created_by')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations principales', {
            'fields': ('name', 'description', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date')
        }),
        ('Gestion', {
            'fields': ('created_by',)
        }),
        ('Dates système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )



@admin.register(ProjectMembership)
class ProjectMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'joined_at')
    list_filter = ('project', 'joined_at')
    search_fields = ('user__username', 'project__name')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'responsible', 'progress', 'start_date', 'end_date')
    list_filter = ('project', 'responsible', 'start_date')
    search_fields = ('name', 'project__name')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'responsible')


@admin.register(SubActivity)
class SubActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'activity', 'assigned_to', 'status', 'created_at')
    list_filter = ('status', 'activity__project', 'assigned_to')
    search_fields = ('name', 'activity__name')
    readonly_fields = ('created_at', 'updated_at')


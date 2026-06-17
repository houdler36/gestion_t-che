from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'assigned_to', 'priority', 'status', 'due_date', 'is_project_task')
    list_filter = ('status', 'priority', 'assigned_to', 'due_date')
    search_fields = ('name', 'description', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'due_date'

    fieldsets = (
        ('Informations', {
            'fields': ('name', 'description', 'sub_activity')
        }),
        ('Assignation', {
            'fields': ('assigned_to', 'created_by')
        }),
        ('Priorité et statut', {
            'fields': ('priority', 'status')
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
    )

    def is_project_task(self, obj):
        return "✅ Oui" if obj.sub_activity else "❌ Non"

    is_project_task.short_description = "Tâche projet"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'assigned_to',
            'created_by',
            'sub_activity'
        )


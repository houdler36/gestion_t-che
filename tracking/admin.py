from django.contrib import admin
from .models import DailyLog


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'task', 'date', 'progress_delta')

    list_filter = ('date', 'user')
    search_fields = ('user__username', 'task__name', 'comment')
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Informations', {
            'fields': ('user', 'task', 'date')
        }),
        ('Suivi', {
            'fields': ('progress_delta',)
        }),

        ('Commentaires', {
            'fields': ('comment', 'difficulties')
        }),
        ('Système', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'task')


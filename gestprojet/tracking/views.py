from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView

from tasks.models import Task
from tracking.models import DailyLog


class DailyLogCreateView(LoginRequiredMixin, CreateView):
    model = DailyLog
    fields = ['task', 'time_spent_minutes', 'progress_delta', 'comment', 'difficulties']
    template_name = 'tracking/log_form.html'
    success_url = reverse_lazy('tracking:log_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Journal enregistré avec succès !')
        return super().form_valid(form)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # ====== Classes Bootstrap pour icônes (input-icon-group) ======
        form.fields['task'].widget.attrs.update({'class': 'form-select'})
        form.fields['time_spent_minutes'].widget.attrs.update({'class': 'form-control'})
        form.fields['progress_delta'].widget.attrs.update({'class': 'form-control'})
        form.fields['comment'].widget.attrs.update({'class': 'form-control'})
        form.fields['difficulties'].widget.attrs.update({'class': 'form-control'})

        form.fields['task'].queryset = Task.objects.filter(assigned_to=self.request.user)
        return form



class DailyLogListView(LoginRequiredMixin, ListView):
    model = DailyLog
    template_name = 'tracking/log_list.html'
    context_object_name = 'logs'

    def get_queryset(self):
        if getattr(self.request.user, 'role', None) == 'ADMIN':
            return DailyLog.objects.all()
        return DailyLog.objects.filter(user=self.request.user)


from django.contrib import admin
from milestones.models import Milestone


class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['article_revision', 'owner', 'title', 'status', 'date',
                    'time']
    search_fields = ('article_revision__title', 'owner__first_name',
                     'owner__last_name', 'title')
    ordering = ['-created']

admin.site.register(Milestone, MilestoneAdmin)

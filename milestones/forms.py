from django import forms
from django.contrib.auth.models import User

from milestones import models
from custom.fields import UserFullNameChoiceField


class MilestoneForm(forms.ModelForm):
    owner = UserFullNameChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('first_name',
                                                              'last_name')
    )
    end_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        self.article = kwargs.pop('article', None)
        self.request = kwargs.pop('request', None)
        kwargs['instance'] = kwargs.pop('instance',
                                        models.Milestone(article=self.article))
        super(MilestoneForm, self).__init__(*args, **kwargs)

    class Meta:
        model = models.Milestone
        widgets = {
            'article': forms.HiddenInput(),
            'article_revision': forms.HiddenInput(),
        }
        exclude = ('deleted',)

    def clean(self):
        cleaned_data = super(MilestoneForm, self).clean()

        if (
            self.cleaned_data.get('end_date')
            and self.cleaned_data.get('end_date')
            <= self.cleaned_data.get('date')
        ):
            raise forms.ValidationError("End date must be greater than "
                                        "start date.")

        return cleaned_data


class MilestoneEditForm(MilestoneForm):
    def __init__(self, *args, **kwargs):
        super(MilestoneEditForm, self).__init__(*args, **kwargs)
        del self.fields['end_date']

    class Meta:
        model = models.Milestone
        widgets = {
            'article': forms.HiddenInput(),
            'article_revision': forms.HiddenInput(),
        }
        fields = ('article', 'article_revision', 'owner', 'title', 'status',
                  'date', 'time', 'deleted')


class MilestonesBatchForm(forms.Form):
    ACTION_CHOICES = (
        (models.Milestone.PENDING_STATUS, 'Set to Pending'),
        (models.Milestone.ACTIVE_STATUS, 'Set to Active'),
        (models.Milestone.COMPLETED_STATUS, 'Set to Completed'),
        (models.Milestone.CANCELLED_STATUS, 'Set to Cancelled'),
        ('delete_action', 'Delete selected milestones'),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(MilestonesBatchForm, self).__init__(*args, **kwargs)

    action = forms.ChoiceField(choices=ACTION_CHOICES)

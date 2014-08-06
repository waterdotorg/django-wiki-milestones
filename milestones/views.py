import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect, render, get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic.edit import FormView

from wiki.decorators import get_article, response_forbidden
from wiki.models.article import ArticleRevision
from wiki.models.urlpath import URLPath
from wiki.views.mixins import ArticleMixin
from milestones import models, settings, forms


class MilestoneView(ArticleMixin, FormView):
    form_class = forms.MilestoneForm
    template_name = "wiki/plugins/milestones/index.html"

    @method_decorator(get_article(can_write=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.milestones = models.Milestone.objects.filter(
            article=article).order_by('date', 'time')
        # Fixing some weird transaction issue caused by adding
        # commit_manually to form_valid
        return super(MilestoneView, self).dispatch(request, article,
                                                   *args, **kwargs)

    def get_automatic_log(self, milestone):
        name = self.request.user.get_full_name()
        if not milestone.pk:
            return _(u"Milestone created by %s. Title: %s" % (name, milestone.title))
        else:
            return _(u"Milestone updated by %s. Title: %s PK: %d" % (name, milestone.pk))

    def form_valid(self, form):
        if (self.request.user.is_anonymous() and not settings.ANONYMOUS or
            not self.article.can_write(self.request.user) or
            self.article.current_revision.locked):
            return response_forbidden(self.request, self.article, self.urlpath)

        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[-1].strip()
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')

        milestone = form.save(commit=False)
        new_revision = ArticleRevision()
        new_revision.inherit_predecessor(milestone.article)
        new_revision.automatic_log = self.get_automatic_log(milestone)
        new_revision.user = self.request.user
        new_revision.ip_address = ip_address
        self.article.add_revision(new_revision)
        milestone.article_revision = self.article.current_revision
        milestone.save()
        form.save_m2m()

        num_copy_day_increment = 1
        start_count = 0
        num_copy = 0
        if form.cleaned_data.get('end_date'):
            num_copy_delta = form.cleaned_data.get('end_date') - form.cleaned_data.get('date')
            num_copy = abs(num_copy_delta.days)

        if num_copy:
            orig_milestone = models.Milestone.objects.get(pk=milestone.pk)
            while start_count < num_copy:
                start_count += 1
                day_increment = num_copy_day_increment * start_count
                new_date = orig_milestone.date + datetime.timedelta(days=day_increment)
                models.Milestone.objects.create(
                    article=orig_milestone.article,
                    article_revision=orig_milestone.article_revision,
                    owner=orig_milestone.owner,
                    title=orig_milestone.title,
                    status=orig_milestone.status,
                    date=new_date,
                )

        if isinstance(milestone, list):
            messages.success(self.request, _(u'Successfully added: %s') % (", ".join([m.title for m in milestone])))
        else:
            messages.success(self.request, _(u'%s was successfully added.') % milestone.title)

        return redirect(self.request.path)

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs['article'] = self.article
        kwargs['request'] = self.request
        return kwargs

    def get_initial(self):
        return {
            'article': self.article,
            'article_revision': self.article.current_revision,
            'date': datetime.date.today(),
            'owner': self.request.user.pk,
        }

    def get_context_data(self, **kwargs):
        kwargs['selected_tab'] = 'milestones'
        kwargs['anonymous_disallowed'] = self.request.user.is_anonymous() and not settings.ANONYMOUS
        kwargs['milestones'] = self.milestones
        return super(MilestoneView, self).get_context_data(**kwargs)


class MilestoneEditView(ArticleMixin, FormView):
    form_class = forms.MilestoneEditForm
    template_name = "wiki/plugins/milestones/index.html"

    @method_decorator(get_article(can_write=True))
    def dispatch(self, request, article, *args, **kwargs):
        self.milestone = get_object_or_404(models.Milestone, pk=kwargs.get('pk'),
            article=article)
        self.milestones = models.Milestone.objects.filter(
            article=article).order_by('date', 'time')

        # Fixing some weird transaction issue caused by adding
        # commit_manually to form_valid
        return super(MilestoneEditView, self).dispatch(request, article,
                                                       *args, **kwargs)

    def get_object(self, queryset=None):
        return self.milestone

    def get_automatic_log(self, milestone):
        name = self.request.user.get_full_name()
        action = u'updated'
        if milestone.deleted:
            action = u'deleted'
        return _(u"Milestone %s by %s. Title: %s PK: %d" % (action, name, milestone.title, milestone.pk))

    def form_valid(self, form):
        if (self.request.user.is_anonymous() and not settings.ANONYMOUS or
            not self.article.can_write(self.request.user) or
            self.article.current_revision.locked):
            return response_forbidden(self.request, self.article, self.urlpath)

        # Get client IP
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[-1].strip()
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')

        milestone = form.save(commit=False)
        new_revision = ArticleRevision()
        new_revision.inherit_predecessor(milestone.article)
        new_revision.automatic_log = self.get_automatic_log(milestone)
        new_revision.user = self.request.user
        new_revision.ip_address = ip_address
        self.article.add_revision(new_revision)
        milestone.article_revision = self.article.current_revision
        milestone.save()
        form.save_m2m()

        if isinstance(milestone, list):
            messages.success(self.request, _(u'Successfully updated: %s') % (", ".join([m.title for m in milestone])))
        else:
            messages.success(self.request, _(u'%s was successfully updated.') % milestone.title)

        #return redirect(self.request.path)
        url_path = URLPath.objects.get(article=self.article.pk)
        redirect_url = '/%s/_plugin/%s/' % (url_path.path, settings.SLUG)
        if not url_path.path:
            redirect_url = '/_plugin/%s/' % settings.SLUG
        return redirect(redirect_url)

    def get_form_kwargs(self):
        kwargs = FormView.get_form_kwargs(self)
        kwargs['article'] = self.article
        kwargs['request'] = self.request
        kwargs['instance'] = self.milestone
        return kwargs

    def get_context_data(self, **kwargs):
        kwargs['selected_tab'] = 'milestones'
        kwargs['anonymous_disallowed'] = self.request.user.is_anonymous() and not settings.ANONYMOUS
        kwargs['milestones'] = self.milestones
        return super(MilestoneEditView, self).get_context_data(**kwargs)


@login_required
def milestones_batch(request):
    form = forms.MilestonesBatchForm(user=request.user)
    milestones = models.Milestone.objects.filter(
        Q(status=models.Milestone.PENDING_STATUS) |
        Q(status=models.Milestone.ACTIVE_STATUS),
        owner=request.user,
        deleted=False,
    ).order_by('date', 'time')

    if request.method == 'POST':
        form = forms.MilestonesBatchForm(request.POST, user=request.user)
        if form.is_valid():
            selected = request.POST.getlist('_selected_action')
            m = models.Milestone.objects.filter(
                ~Q(owner=request.user),
                pk__in=selected,
            )
            if m.count():
                messages.error(request, u'Milestone ownership error. You are not currently the owner of all submitted milestones.')
            else:
                selected_milestones = models.Milestone.objects.filter(
                    id__in=selected
                )
                if form.cleaned_data['action'] == 'delete_action':
                    selected_milestones.update(deleted=True)
                    messages.success(request, u'Milestones deleted')
                else:
                    selected_milestones.update(status=int(form.cleaned_data['action']))
                    messages.success(request, u'Milestones updated')
            return redirect(request.path)

    dict_context = {'form': form, 'milestones': milestones}

    return render(request, 'milestones/batch.html', dict_context)


def get_color_dict():
    color_dict = {}
    colors = ['#555555', '#cccccc', '#56a83c', '#a73111', '#10845a', '#003366',
              '#511000', '#0000ff', '#336699', '#918010', '#9999ff', '#99ccff',
              '#cc0000', '#6699cc', '#123456', '#906090', '#ff6600', '#ff8d8d',
              '#ff9900', '#82cccd', '#3b5998', '#0066cc', '#00dd00', '#00cbcd',
              '#9999cc', '#333366', '#006600', '#9c00ff', '#d900dc', '#dc8c00',
              '#4cc6ff', '#9c4cff', '#bf5b5b', '#bfb95b', '#9dbf5b', '#640005']
    user_qs = User.objects.filter(is_active=True,
                                  is_staff=False).order_by('first_name')
    for user in user_qs:
        try:
            color_dict[user.pk] = colors.pop()
        except IndexError:
            color_dict[user.pk] = '#cccccc'

    return color_dict


@login_required
def milestones_calendar(request):
    users = []
    user_qs = User.objects.filter(is_active=True,
                                  is_staff=False).order_by('first_name')
    color_dict = get_color_dict()

    for user in user_qs:
        user.color = color_dict[user.pk]
        users.append(user)

    article_pk = request.GET.get('apk', '')

    dict_context = {'users': users, 'article_pk': article_pk}
    return render(request, 'milestones/calendar.html', dict_context)


@login_required
def milestones_calendar_json(request):
    color_dict = get_color_dict()
    start_date = datetime.datetime.fromtimestamp(
        float(request.GET.get('start', 0.0))
    )
    end_date = datetime.datetime.fromtimestamp(
        float(request.GET.get('end', 0.0))
    )
    milestone_qs = (models.Milestone.objects.select_related()
                    .exclude(Q(status=models.Milestone.CANCELLED_STATUS) | Q(deleted=True))
                    .filter(date__gte=start_date, date__lte=end_date))

    article_pk = request.GET.get('apk')
    if article_pk:
        milestone_qs = milestone_qs.filter(article__pk=article_pk)

    milestones = []
    for milestone in milestone_qs:
        milestone.color = color_dict[milestone.owner.pk]
        milestones.append(milestone)

    dict_context = {'milestones': milestones}
    calendar_event_json = render_to_string('milestones/calendar.json',
                                           dict_context)
    return HttpResponse(calendar_event_json, mimetype="application/json")

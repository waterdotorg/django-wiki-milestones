# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url
from django.utils.translation import ugettext as _

from wiki.core.plugins import registry
from wiki.core.plugins.base import BasePlugin
from wiki.plugins.notifications.settings import ARTICLE_EDIT
from wiki.plugins.notifications.util import truncate_title

from milestones import settings, models, views
from milestones.markdown_extensions import MilestoneExtension


class MilestonePlugin(BasePlugin):
    slug = settings.SLUG
    urlpatterns = {
        'article': patterns('',
            url(r'^$', views.MilestoneView.as_view(), name='milestone'),
            url(r'^edit/(?P<pk>\d+)/$', views.MilestoneEditView.as_view(),
                name='milestone_edit'),
        )
    }
    article_tab = (_(u'Milestones'), "icon-tasks")
    article_view = views.MilestoneView().dispatch

    """
    ###
    This is now hardcoded in templates/wiki/plugins/macros/sidebar.html
    ###

    sidebar = {'headline': _('Milestones'),
               'icon_class': 'icon-tasks',
               'template': 'wiki/plugins/milestones/sidebar.html',
               'form_class': None,
               'get_form_kwargs': (lambda a: {})}
    """

    # List of notifications to construct signal handlers for. This
    # is handled inside the notifications plugin.
    notifications = [
        {'model': models.Milestone,
         'message': lambda obj: _(u"A milestone was added: %s") % truncate_title(obj.title),
         'key': ARTICLE_EDIT,
         'created': True,
         'get_article': lambda obj: obj.article}
    ]

    markdown_extensions = [MilestoneExtension()]

registry.register(MilestonePlugin)

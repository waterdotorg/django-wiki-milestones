# -*- coding: utf-8 -*-
import datetime
import markdown
import re

from django.db.models import Q
from django.template.loader import render_to_string
from django.template import Context
from milestones import models


MILESTONE_RE = re.compile(r'.*(\[milestones(\s+owner\:(?P<owner>\w+))?(\s+days\:(?P<days>\d+))?(\s+start_date\:(?P<start_date>[-\w]+))?(\s+end_date\:(?P<end_date>[-\w]+))?\s*\]).*',
                          re.IGNORECASE)


class MilestoneExtension(markdown.Extension):
    """ Milestones plugin markdown extension for django-wiki. """

    def extendMarkdown(self, md, md_globals):
        """ Insert MilestonePreprocessor before ReferencePreprocessor. """
        md.preprocessors.add('dw-milestones', MilestonePreprocessor(md),
                             '>html_block')


class MilestonePreprocessor(markdown.preprocessors.Preprocessor):
    """
    django-wiki milestone preprocessor - parse text for
    [milestones owner:username days:30] references.
    """

    def run(self, lines):
        new_text = []
        milestones = None
        owner = None
        days = 30
        start_date = None
        today = datetime.date.today()
        filter_kwargs = {'deleted': False}
        for line in lines:
            m = MILESTONE_RE.match(line)
            if m:
                owner = m.group('owner')
                if owner:
                    filter_kwargs.update({'owner__username': owner.strip()})

                start_date = m.group('start_date')
                if start_date:
                    filter_kwargs.update({'date__gte': start_date})

                end_date = m.group('end_date')
                if end_date:
                    filter_kwargs.update({'date__lte': end_date})

                if not start_date and not end_date:
                    if m.group('days'):
                        days = int(m.group('days'))
                    filter_kwargs.update({
                        'date__lte': today + datetime.timedelta(days=days)
                    })

                milestones = (
                    models.Milestone.objects
                    .filter(
                        Q(status=models.Milestone.PENDING_STATUS) |
                        Q(status=models.Milestone.ACTIVE_STATUS) |
                        Q(status=models.Milestone.INFORMATIONAL_STATUS),
                        **filter_kwargs)
                    .exclude(
                        status=models.Milestone.INFORMATIONAL_STATUS,
                        date__lt=today)
                    .order_by('date', 'time'))

                html = render_to_string(
                    "wiki/plugins/milestones/fragments/milestones.html",
                    Context({'milestones': milestones,
                    'display_milestone_page_title': True})
                )
                html_stash = self.markdown.htmlStash.store(html, safe=True)
                line = line.replace(m.group(1), html_stash)
            new_text.append(line)
        return new_text

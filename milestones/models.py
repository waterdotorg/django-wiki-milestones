import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from wiki.models.pluginbase import SimplePlugin, SimplePluginCreateError


class Milestone(SimplePlugin):
    PENDING_STATUS = 0
    ACTIVE_STATUS = 1
    COMPLETED_STATUS = 2
    CANCELLED_STATUS = 3
    INFORMATIONAL_STATUS = 4

    STATUS_CHOICES = (
        (PENDING_STATUS, 'Pending'),
        (ACTIVE_STATUS, 'Active'),
        (COMPLETED_STATUS, 'Completed'),
        (CANCELLED_STATUS, 'Cancelled'),
        (INFORMATIONAL_STATUS, 'Informational'),
    )
    owner = models.ForeignKey(settings.AUTH_USER_MODEL)
    title = models.CharField(max_length=200)
    status = models.SmallIntegerField(choices=STATUS_CHOICES,
                                      default=ACTIVE_STATUS)
    date = models.DateField()
    time = models.TimeField(blank=True, null=True)

    class Meta:
        verbose_name = _(u'milestone')
        verbose_name_plural = _(u'milestones')

    def __unicode__(self):
        return "%s" % self.title

    def get_overdue_class(self):
        if (
                self.date < datetime.date.today()
                and not self.status == self.INFORMATIONAL_STATUS
           ):
            return 'danger'
        return

    def get_status_class(self):
        today = datetime.date.today()
        append = u''
        status = u''

        if self.deleted:
            append = u' deleted'

        """
        if self.status == self.PENDING_STATUS:
            status = 'warning'
        elif self.status == self.ACTIVE_STATUS:
            status = 'info'
        elif self.status == self.COMPLETED_STATUS:
            status = 'success'
        else:
            status = 'error'
        """

        if (
                self.status == self.COMPLETED_STATUS or
                self.status == self.CANCELLED_STATUS or
                self.deleted or
                self.status == self.INFORMATIONAL_STATUS and
                self.date < today
           ):
            # do:
            append += u' default-hide'

        return u'%s%s' % (status, append)

    def get_status(self):
        for c in self.STATUS_CHOICES:
            if self.status == c[0]:
                return c[1]

    def save(self, *args, **kwargs):
        if not self.id:
            if not self.article.current_revision:
                raise SimplePluginCreateError("Article does not have a current_revision set.")
        super(SimplePlugin, self).save(*args, **kwargs)

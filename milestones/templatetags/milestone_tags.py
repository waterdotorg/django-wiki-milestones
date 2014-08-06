from django import template

from milestones import models

register = template.Library()

@register.filter
def milestones_for_article(article):
    return models.Milestone.objects.filter(article=article).order_by('date', 'time')

@register.filter
def milestones_can_add(article, user):
    return article.can_write(user)

import uuid

from django.db import models


class Testee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    age = models.PositiveIntegerField(verbose_name='Возраст')
    # TODO - other demographic fields

    class Meta:
        verbose_name = 'Испытуемый'
        verbose_name_plural = 'Испытуемые'


class ContextSet(models.Model):
    """ A set of contexts to be grouped.
    """
    word = models.TextField()
    order = models.FloatField()

    class Meta:
        verbose_name = 'Набор контекстов для слова'
        verbose_name_plural = 'Наборы контекстов для слов'
        ordering = ['order']

    def __str__(self):
        return self.word


class Context(models.Model):
    text = models.TextField()
    context_set = models.ForeignKey(ContextSet)

    class Meta:
        verbose_name = 'Контекст'
        verbose_name_plural = 'Контексты'

    def __str__(self):
        return '{} ({})'.format(self.text, self.context_set)


class ContextGroup(models.Model):
    """ A grouping of contexts by the testee.
    """
    testee = models.ForeignKey(Testee)
    context_set = models.ForeignKey(ContextSet)
    contexts = models.ManyToManyField(Context)

    class Meta:
        unique_together = [['testee', 'context_set']]
        verbose_name = 'Группировка контекстов'
        verbose_name_plural = 'Группировки контекстов'

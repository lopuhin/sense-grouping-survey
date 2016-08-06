import uuid

from django.db import models


class Named(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class LeadingHand(Named):
    pass


class Sex(Named):
    pass


class Education(Named):
    pass


class Speciality(Named):
    pass


class Participant(models.Model):
    """ Survey participant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speciality = models.ForeignKey(Speciality, verbose_name='Образование')
    age = models.PositiveIntegerField(verbose_name='Возраст')
    leading_hand = models.ForeignKey(LeadingHand, verbose_name='Ведущая рука')
    sex = models.ForeignKey(Sex, verbose_name='Пол')
    languages = models.TextField(
        verbose_name='Родной язык/языки',
        help_text='пожалуйста, перечислите все')
    education = models.ForeignKey(
        Education, verbose_name='Последняя законченная ступень образования')

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
    """ A grouping of contexts by a participant.
    """
    participant = models.ForeignKey(Participant)
    context_set = models.ForeignKey(ContextSet)
    contexts = models.ManyToManyField(Context)

    class Meta:
        unique_together = [['participant', 'context_set']]
        verbose_name = 'Группировка контекстов'
        verbose_name_plural = 'Группировки контекстов'

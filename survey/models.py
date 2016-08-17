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


class Participant(models.Model):
    """ Survey participant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    started = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(auto_now=True)
    profession = models.TextField(verbose_name='Образование')
    age = models.PositiveIntegerField(verbose_name='Возраст')
    leading_hand = models.ForeignKey(LeadingHand, verbose_name='Ведущая рука')
    sex = models.BooleanField(verbose_name='Пол')
    languages = models.TextField(
        verbose_name='Родной язык/языки',
        help_text='пожалуйста, перечислите все')
    education = models.ForeignKey(
        Education, verbose_name='Последняя законченная ступень образования')
    email = models.TextField(blank=True, default='')
    feedback = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Испытуемый'
        verbose_name_plural = 'Испытуемые'
        ordering = ['finished']

    def __str__(self):
        return str(self.id)


class ContextSet(models.Model):
    """ A set of contexts to be grouped.
    """
    word = models.TextField()

    class Meta:
        verbose_name = 'Набор контекстов для слова'
        verbose_name_plural = 'Наборы контекстов для слов'

    def __str__(self):
        return self.word


class Context(models.Model):
    context_set = models.ForeignKey(ContextSet)
    order = models.FloatField()
    text = models.TextField()

    class Meta:
        verbose_name = 'Контекст'
        verbose_name_plural = 'Контексты'
        ordering = ['order']

    def __str__(self):
        return '{} ({})'.format(self.text, self.context_set)


class ContextGroup(models.Model):
    """ A grouping of contexts by a participant.
    """
    participant = models.ForeignKey(Participant)
    context_set = models.ForeignKey(ContextSet)
    contexts = models.ManyToManyField(Context)

    class Meta:
        verbose_name = 'Группировка контекстов'
        verbose_name_plural = 'Группировки контекстов'

    def __str__(self):
        return '{} {}'.format(self.context_set, self.participant)

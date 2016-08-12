from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.views import static

import survey.views


urlpatterns = [
    url(r'^$', survey.views.Start.as_view(), name='start_survey'),
    url(r'^group/([\w\-]+)/$', survey.views.Group.as_view(),
        name='survey_step'),
    url(r'^feedback/([\w\-]+)/$', survey.views.survey_feedback,
        name='survey_feedback'),
    url(r'^finish/$', survey.views.finish_survey, name='finish_survey'),
    url(r'^admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT,
         'show_indexes': settings.DEBUG}),

]

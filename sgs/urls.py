from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.views import static

import survey.views


urlpatterns = [
    url(r'^$', survey.views.start_survey, name='start_survey'),
    url(r'^group/([\w\-]+)/(\d+)/$',
        survey.views.survey_step, name='survey_step'),
    url(r'^finish/$', survey.views.finish_survey, name='finish_survey'),
    url(r'^admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT,
         'show_indexes': settings.DEBUG}),

]

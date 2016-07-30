from django.conf import settings
from django.conf.urls import url
from django.contrib import admin

import survey.views


urlpatterns = [
    url(r'^$', survey.views.start_survey, name='start_survey'),
    url(r'^group/([\w\-]+)/(\d+)/$',
        survey.views.survey_step, name='survey_step'),
    url(r'^admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_ROOT, 'show_indexes': settings.DEBUG}),
]

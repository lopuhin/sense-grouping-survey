from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.views import static

import survey.views


urlpatterns = [
    url(r'^$', survey.views.Start.as_view(), name='start_survey'),
    url(r'^group/([\w\-]+)/$', survey.views.Group.as_view(),
        name='survey_step'),
    url(r'^feedback/([\w\-]+)/$', survey.views.Feedback.as_view(),
        name='survey_feedback'),
    url(r'^export/$', survey.views.Export.as_view(),
        name='survey_export'),
    url(r'^stats/$', survey.views.Stats.as_view(),
        name='survey_stats'),
    url(r'^admin/', admin.site.urls),
    url(r'^static/(?P<path>.*)$', static.serve,
        {'document_root': settings.STATIC_ROOT,
         'show_indexes': settings.DEBUG}),

]

from django.contrib import admin

from .models import Context, ContextGroup, ContextSet, Participant


admin.site.register(Participant)
admin.site.register(Context)
admin.site.register(ContextGroup)
admin.site.register(ContextSet)

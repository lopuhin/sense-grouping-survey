from django.contrib import admin

from .models import Context, ContextGroup, ContextSet, Testee


admin.site.register(Testee)
admin.site.register(Context)
admin.site.register(ContextGroup)
admin.site.register(ContextSet)

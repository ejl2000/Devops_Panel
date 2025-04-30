from devopspanel.core.models import ServiceButton, ServiceGroup, Environment, ServiceButtonLink, CodeBase, CodeBaseDependency, BearerToken, SubGroup
from django.contrib import admin
from devopspanel.users.models import CustomUser, Role
from devopspanel.core.models import Tag
from django.contrib.auth.admin import UserAdmin
from devopspanel.dashboard.forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.admin.sites import NotRegistered

admin.site.register(ServiceButton)
admin.site.register(ServiceGroup)
admin.site.register(Environment)
admin.site.register(ServiceButtonLink)
admin.site.register(CodeBase)
admin.site.register(CodeBaseDependency)
admin.site.register(BearerToken)
admin.site.register(SubGroup)

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'is_staff', 'is_active']
    list_filter = ['is_staff', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('environments', 'service_groups')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('environments', 'service_groups')}),
    )

class ServiceButtonAdmin(admin.ModelAdmin):
    list_display = ['name', 'environment', 'created_by', 'ip', 'port', 'version', 'location']
    list_filter = ['environment', 'groups', 'tags', 'location']
    search_fields = ['name', 'description', 'ip', 'port', 'version']
    filter_horizontal = ('groups', 'connections')

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'tags':
            kwargs['widget'] = admin.widgets.FilteredSelectMultiple('Tags', False)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

class TagAdmin(admin.ModelAdmin):
    pass

try:
    admin.site.unregister(Tag)
except NotRegistered:
    pass

admin.site.register(Tag, TagAdmin)

from django.contrib import admin
from taggit.models import Tag as TaggitTag

try:
    admin.site.unregister(TaggitTag)
except admin.sites.NotRegistered:
    pass
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from devopspanel.core.models import ServiceButton, ServiceGroup, Environment, ServiceButtonLink, CodeBase, CodeBaseDependency, SubGroup, Tag, Maintenance
from django_select2.forms import Select2TagWidget, Select2MultipleWidget, Select2Widget
from django.forms import inlineformset_factory
from taggit.forms import TagField
from django.core.exceptions import ValidationError
import json
import re
import logging
import pytz
from django.urls import get_resolver, URLPattern, URLResolver
from django.contrib.auth import get_user_model
from django_select2.forms import ModelSelect2MultipleWidget
from devopspanel.users.models import Role, Permission
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column, Button, Fieldset
from crispy_forms.bootstrap import FormActions
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.conf import settings
from django import forms
from devopspanel.core.models import ServiceButton
from devopspanel.core.widgets import TaggableSelectWidget
from django.forms import ModelForm, DateTimeInput, CheckboxSelectMultiple

logger = logging.getLogger(__name__)

User = get_user_model()

ICON_CHOICES = [
    ('fas fa-home', 'Home'),
    ('fas fa-user', 'User'),
    ('fas fa-cog', 'Settings'),
    ('fa-asterisk', 'Asterisk'),
    ('fa-server', 'Server'),
]

LOCATION_CHOICES = [
    ('K8S', 'K8S'),
    ('VM-GCP', 'VM-GCP'),
    ('Bare-Metal', 'Bare-Metal'),
    ('Cloud-SQL', 'Cloud-SQL'),
    ('CloudFlare', 'CloudFlare'),
]

def get_all_view_paths(urlpatterns=None, prefix=''):
    if urlpatterns is None:
        resolver = get_resolver()
        urlpatterns = resolver.url_patterns
    view_paths = []
    for pattern in urlpatterns:
        if isinstance(pattern, URLPattern):
            callback = pattern.callback
            if hasattr(callback, 'view_class'):
                view_class = callback.view_class
                view_path = f"{view_class.__module__}.{view_class.__name__}"
            else:
                view_path = f"{callback.__module__}.{callback.__name__}"
            view_paths.append((view_path, view_path))
        elif isinstance(pattern, URLResolver):
            view_paths += get_all_view_paths(pattern.url_patterns, prefix=prefix + pattern.pattern.regex.pattern)
    return view_paths

class UserProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    emergency_phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.all_timezones],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'emergency_phone', 'timezone', 'avatar']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

class CustomPasswordChangeForm(forms.Form):
    new_password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='New Password',
        help_text='Your password must contain at least 1 digit, 1 uppercase letter, and 1 special character.'
    )
    new_password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm New Password'
    )

    def __init__(self, user, *args, **kwargs):
        super(CustomPasswordChangeForm, self).__init__(*args, **kwargs)
        self.user = user

    def clean_new_password1(self):
        new_password = self.cleaned_data.get('new_password1')
        if new_password:
            if len(new_password) < 8:
                raise ValidationError("Password must be at least 8 characters long.")
            if not re.search(r'\d', new_password):
                raise ValidationError("Password must contain at least one digit.")
            if not re.search(r'[A-Z]', new_password):
                raise ValidationError("Password must contain at least one uppercase letter.")
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
                raise ValidationError("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>).")
        return new_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2 and new_password1 != new_password2:
            raise ValidationError("The two password fields didn't match.")
        return new_password2

    def save(self, commit=True):
        new_password = self.cleaned_data.get('new_password1')
        self.user.set_password(new_password)
        if commit:
            self.user.save()
        return self.user

class CodeBaseForm(forms.ModelForm):
    class Meta:
        model = CodeBase
        fields = ['name', 'url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CodeBaseDependencyForm(forms.ModelForm):
    class Meta:
        model = CodeBaseDependency
        fields = ['name', 'url', 'dependencies']  # Удалили 'id'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'dependencies': Select2MultipleWidget(attrs={'class': 'form-control select2'}),
        }

CodeBaseDependencyFormSetCreate = inlineformset_factory(
    CodeBase,
    CodeBaseDependency,
    form=CodeBaseDependencyForm,
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True
)

CodeBaseDependencyFormSetEdit = inlineformset_factory(
    CodeBase,
    CodeBaseDependency,
    form=CodeBaseDependencyForm,
    extra=0,
    can_delete=True,
    max_num=10,
    validate_max=True
)

class PermissionForm(forms.ModelForm):
    view_name = forms.ChoiceField(
        choices=[],
        required=True,
        label='View',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = Permission
        fields = ['name', 'codename', 'description', 'view_name']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super(PermissionForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='form-group col-md-4 mb-0'),
                Column('codename', css_class='form-group col-md-4 mb-0'),
                Column('view_name', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            'description',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                Button('cancel', 'Cancel', css_class='btn btn-secondary',
                       onclick="window.location.href='{% url 'core:permission_list' %}'")
            )
        )

        self.fields['view_name'].choices = self.get_view_choices()

    def get_view_choices(self):
        resolver = get_resolver()
        views = self.get_all_view_names(resolver)
        choices = [('', '---------')]
        for view_name in views:
            if view_name.endswith(':*'):
                label = f"All views in {view_name[:-2]}"
            else:
                label = view_name
            choices.append((view_name, label))
        return choices

    def get_all_view_names(self, resolver, prefix=''):
        view_names = []
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLPattern):
                if pattern.name:
                    full_view_name = f"{prefix}:{pattern.name}" if prefix else pattern.name
                    view_names.append(full_view_name)
            elif isinstance(pattern, URLResolver):
                sub_prefix = f"{prefix}:{pattern.namespace}" if prefix and pattern.namespace else pattern.namespace or prefix
                view_names += self.get_all_view_names(pattern, prefix=sub_prefix)
        return view_names

    def clean_view_name(self):
        view_name = self.cleaned_data.get('view_name')
        if not view_name:
            raise forms.ValidationError("This field is required.")
        return view_name

class RoleForm(forms.ModelForm):
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Description'
    )
    wildcard_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.filter(view_name__endswith=':*'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        label='Wildcard Permissions'
    )
    specific_permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.exclude(view_name__endswith=':*'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        label='Specific Permissions'
    )

    class Meta:
        model = Role
        fields = ['name', 'description', 'wildcard_permissions', 'specific_permissions']

    def __init__(self, *args, **kwargs):
        self.cancel_url = kwargs.pop('cancel_url', '')
        super(RoleForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['wildcard_permissions'].initial = self.instance.permissions.filter(view_name__endswith=':*')
            self.fields['specific_permissions'].initial = self.instance.permissions.exclude(view_name__endswith=':*')

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'name',
            'description',
            Fieldset(
                'Permissions',
                'wildcard_permissions',
                'specific_permissions',
            ),
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                Button('cancel', 'Cancel', css_class='btn btn-secondary', onclick=f"window.location.href='{self.cancel_url}'")
            )
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            permissions = list(self.cleaned_data['wildcard_permissions']) + list(self.cleaned_data['specific_permissions'])
            instance.permissions.set(permissions)
        return instance

class ServiceButtonLinkForm(forms.ModelForm):
    class Meta:
        model = ServiceButtonLink
        fields = ['name', 'url', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'location': Select2Widget(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super(ServiceButtonLinkForm, self).__init__(*args, **kwargs)
        self.fields['name'].required = False
        self.fields['url'].required = False
        self.fields['location'].required = False

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        url = cleaned_data.get('url')
        location = cleaned_data.get('location')

        if name or url or location:
            if not name:
                self.add_error('name', 'This field is required.')
            if not url:
                self.add_error('url', 'This field is required.')
            if not location:
                self.add_error('location', 'This field is required.')
        else:
            self.cleaned_data['DELETE'] = True

        return cleaned_data

ServiceButtonLinkFormSet = inlineformset_factory(
    ServiceButton,
    ServiceButtonLink,
    form=ServiceButtonLinkForm,
    extra=1,
    can_delete=True,
    max_num=10,
    validate_max=True
)

class ServiceButtonForm(forms.ModelForm):
    icon_choice = forms.ChoiceField(
        choices=ICON_CHOICES,
        required=False,
        label='Choose Icon',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    custom_icon = forms.ImageField(
        required=False,
        label='Or Upload Your Own Icon',
        help_text='Recommended icon size: 50x50 px.'
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=ServiceGroup.objects.all(),
        required=False,
        label='Groups',
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    subgroup = forms.ModelChoiceField(
        queryset=SubGroup.objects.none(),
        required=False,
        label='SubGroup',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    environment = forms.ModelChoiceField(
        queryset=Environment.objects.all(),
        required=True,
        label='Environment',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=Select2MultipleWidget(
            attrs={'class': 'form-control select2', 'data-placeholder': 'Select or add tags'}),
        label='Tags',
        help_text='Select existing tags or add new ones.'
    )
    connections = forms.ModelMultipleChoiceField(
        queryset=ServiceButton.objects.all(),
        required=False,
        label='Connections',
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )
    executive = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label='Executive',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    ip = forms.GenericIPAddressField(
        required=False,
        label='IP Address',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Internal IP address of the service.'
    )
    port = forms.IntegerField(
        required=False,
        label='Port',
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Port number of the service.'
    )
    version = forms.CharField(
        required=False,
        label='Version',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Version of the service.'
    )
    location = forms.ChoiceField(
        choices=LOCATION_CHOICES,
        required=True,
        label='Location',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )
    is_multi_link = forms.BooleanField(
        required=False,
        label='Enable Multiple Links',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    has_code_base = forms.BooleanField(
        required=False,
        label='Has Code Base',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    code_base_name = forms.CharField(
        required=False,
        label='Code Base Name',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    code_base_url = forms.URLField(
        required=False,
        label='Code Base URL',
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    has_code_base_dependencies = forms.BooleanField(
        required=False,
        label='Has Code Base Dependencies',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    dev_language = forms.ChoiceField(
        choices=ServiceButton.DEV_LANGUAGE_CHOICES,
        required=False,
        label='Development Language',
        widget=forms.Select(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = ServiceButton
        fields = [
            'name', 'description', 'url',
            'icon_choice', 'custom_icon', 'tags',
            'groups', 'subgroup', 'dev_language',
            'environment', 'connections', 'executive',
            'ip', 'port', 'version', 'location',
            'is_multi_link', 'has_code_base',
            'code_base_name', 'code_base_url',
            'has_code_base_dependencies',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user and not self.user.is_staff:
            if 'environment' in self.fields:
                self.fields['environment'].queryset = self.user.environments.all()
            if 'groups' in self.fields:
                self.fields['groups'].queryset = ServiceGroup.objects.filter(
                    environment__in=self.user.environments.all()
                )
            if 'connections' in self.fields:
                self.fields['connections'].queryset = ServiceButton.objects.filter(
                    environment__in=self.user.environments.all()
                ).exclude(id=self.instance.id if self.instance else None)
            if 'executive' in self.fields:
                self.fields['executive'].queryset = User.objects.filter(
                    environments__in=self.user.environments.all()
                ).distinct()

        if self.user:
            permissions_to_remove = [
                'core.edit_servicebutton_description',
                'core.edit_servicebutton_tags',
                'core.edit_servicebutton_repository',
                'core.edit_servicebutton_port',
                'core.edit_servicebutton_version',
                'core.edit_servicebutton_url',
                'core.edit_servicebutton_icon',
                'core.edit_servicebutton_groups',
                'core.edit_servicebutton_location',
                'core.edit_servicebutton_connections',
                'core.edit_servicebutton_executive',
                'core.edit_servicebutton_name',
                'core.edit_servicebutton_environment',
                'core.edit_servicebutton_dev_language',
            ]

            for perm in permissions_to_remove:
                if not self.user.has_perm(perm):
                    field_name = perm.split('.')[-1]
                    self.fields.pop(field_name, None)

        if 'groups' in self.fields and 'subgroup' in self.fields:
            if self.instance.pk and self.instance.groups.exists():
                selected_groups = self.instance.groups.all()
                self.fields['subgroup'].queryset = SubGroup.objects.filter(group__in=selected_groups)
                if self.instance.subgroup:
                    self.fields['subgroup'].initial = self.instance.subgroup
            else:
                self.fields['subgroup'].queryset = SubGroup.objects.none()

        if 'url' in self.fields:
            self.fields['url'].required = False

        if self.instance.pk:
            self.fields['tags'].initial = self.instance.tags.all()

        if self.instance.pk and self.instance.code_base:
            if 'has_code_base' in self.fields:
                self.fields['has_code_base'].initial = True
            if 'code_base_name' in self.fields:
                self.fields['code_base_name'].initial = self.instance.code_base.name
            if 'code_base_url' in self.fields:
                self.fields['code_base_url'].initial = self.instance.code_base.url
            if 'has_code_base_dependencies' in self.fields:
                self.fields['has_code_base_dependencies'].initial = self.instance.code_base.dependencies.exists()
        else:
            if 'has_code_base' in self.fields:
                self.fields['has_code_base'].initial = False
            if 'has_code_base_dependencies' in self.fields:
                self.fields['has_code_base_dependencies'].initial = False

        if ('groups' in self.fields
                and 'subgroup' in self.fields
                and 'groups' in self.data):
            group_ids = self.data.getlist('groups')
            self.fields['subgroup'].queryset = SubGroup.objects.filter(group__id__in=group_ids)

    def clean_tags(self):
        tags = self.cleaned_data.get('tags', [])

        tag_names = list(dict.fromkeys([tag.name.strip() for tag in tags if tag.name.strip()]))

        cleaned_tags = Tag.objects.filter(name__in=tag_names)

        logger.debug(f"Clear list of tags after processing: {tag_names}")
        return cleaned_tags

    def clean(self):
        cleaned_data = super().clean()
        if 'has_code_base' in self.fields:
            has_code_base = cleaned_data.get('has_code_base', False)
            code_base_name = cleaned_data.get('code_base_name', '')
            code_base_url = cleaned_data.get('code_base_url', '')

            if has_code_base:
                if not code_base_name.strip():
                    self.add_error('code_base_name', 'This field is required when "Has Code Base" is selected.')
                if not code_base_url.strip():
                    self.add_error('code_base_url', 'This field is required when "Has Code Base" is selected.')
            else:
                if 'code_base_name' in cleaned_data:
                    cleaned_data['code_base_name'] = ''
                if 'code_base_url' in cleaned_data:
                    cleaned_data['code_base_url'] = ''

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.user:
            permissions_to_keep = [
                'core.edit_servicebutton_description',
                'core.edit_servicebutton_tags',
                'core.edit_servicebutton_repository',
                'core.edit_servicebutton_port',
                'core.edit_servicebutton_version',
                'core.edit_servicebutton_url',
                'core.edit_servicebutton_icon',
                'core.edit_servicebutton_groups',
                'core.edit_servicebutton_location',
                'core.edit_servicebutton_connections',
                'core.edit_servicebutton_executive',
                'core.edit_servicebutton_name',
                'core.edit_servicebutton_environment',
                'core.edit_servicebutton_dev_language',
            ]

            permissions_to_pop = [
                perm for perm in permissions_to_keep if not self.user.has_perm(perm)
            ]

            for perm in permissions_to_pop:
                field_name = perm.split('.')[-1]
                if hasattr(instance, field_name):
                    setattr(instance, field_name, getattr(self.instance, field_name))

        if 'has_code_base' in self.fields:
            has_code_base = self.cleaned_data.get('has_code_base', False)
            code_base_name = self.cleaned_data.get('code_base_name', '')
            code_base_url = self.cleaned_data.get('code_base_url', '')

            if has_code_base:
                if instance.code_base:
                    code_base = instance.code_base
                    code_base.name = code_base_name
                    code_base.url = code_base_url
                    code_base.save()
                else:
                    code_base = CodeBase.objects.create(name=code_base_name, url=code_base_url)
                    instance.code_base = code_base
            else:
                if instance.code_base:
                    instance.code_base.dependencies.all().delete()
                    instance.code_base.delete()
                    instance.code_base = None

        if 'subgroup' in self.fields:
            instance.subgroup = self.cleaned_data.get('subgroup')

        if commit:
            instance.save()
            self.save_m2m()

            tags = self.cleaned_data.get('tags', [])
            if tags:
                instance.tags.set(tags)
            else:
                instance.tags.clear()

        return instance

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class GroupForm(forms.ModelForm):
    class Meta:
        model = ServiceGroup
        fields = ['name', 'environment']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'environment': Select2Widget(attrs={'class': 'form-control select2'}),
        }

class SubGroupForm(forms.ModelForm):
    class Meta:
        model = SubGroup
        fields = ['name', 'group']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'group': Select2Widget(attrs={'class': 'form-control select2'}),
        }

    def __init__(self, *args, **kwargs):
        super(SubGroupForm, self).__init__(*args, **kwargs)
        self.fields['group'].label_from_instance = lambda obj: f"{obj.name} ({obj.environment.name})"

class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = Environment
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    emergency_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Permissions'
    )
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.all_timezones],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'form-control select2'}),
        label='Roles'
    )
    environments = forms.ModelMultipleChoiceField(
        queryset=Environment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Environments'
    )
    service_groups = forms.ModelMultipleChoiceField(
        queryset=ServiceGroup.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Groups'
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Avatar'
    )
    is_staff = forms.BooleanField(required=False, label='Administrator')
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'password1', 'password2',
            'emergency_phone', 'timezone', 'roles', 'permissions',
            'is_staff', 'environments', 'service_groups'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super(CustomUserCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.emergency_phone = self.cleaned_data.get('emergency_phone')
        user.timezone = self.cleaned_data.get('timezone')
        user.is_staff = self.cleaned_data.get('is_staff')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        if commit:
            user.save()
            self.save_m2m()
            user.permissions.set(self.cleaned_data['permissions'])
        return user

class CustomUserChangeForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    emergency_phone = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Разрешения'
    )
    timezone = forms.ChoiceField(
        choices=[(tz, tz) for tz in pytz.all_timezones],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'form-control select2'}),
        label='Roles'
    )
    environments = forms.ModelMultipleChoiceField(
        queryset=Environment.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Environments'
    )
    service_groups = forms.ModelMultipleChoiceField(
        queryset=ServiceGroup.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Groups'
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'}),
        label='Avatar'
    )
    is_staff = forms.BooleanField(required=False, label='Administrator')
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email', 'emergency_phone', 'timezone', 'roles',
            'permissions', 'is_staff', 'environments', 'service_groups'
        ]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserChangeForm, self).__init__(*args, **kwargs)
        self.fields['service_groups'].label_from_instance = lambda obj: f"{obj.name} ({obj.environment.name if obj.environment else 'No Environment'})"

    def save(self, commit=True):
        user = super(CustomUserChangeForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.emergency_phone = self.cleaned_data.get('emergency_phone')
        user.timezone = self.cleaned_data.get('timezone')
        user.is_staff = self.cleaned_data.get('is_staff')
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        if commit:
            user.save()
            self.save_m2m()
            user.permissions.set(self.cleaned_data['permissions'])
        return user

class APIKeyCreateForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I confirm that I want to generate a new API key.",
    )


class MaintenanceForm(ModelForm):
    service_buttons = forms.ModelMultipleChoiceField(
        queryset=ServiceButton.objects.all(),
        required=False,
        widget=Select2MultipleWidget(
            attrs={'class': 'form-control select2', 'data-placeholder': 'Select or add tags'}),
        label='Service Buttons',
        help_text = 'Select existing Service.'
    )

    class Meta:
        model = Maintenance
        fields = ['title', 'description', 'start_time', 'end_time', 'status', 'executive', 'service_buttons']
        widgets = {
            'start_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'end_time': DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}, format='%Y-%m-%dT%H:%M'),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'executive': forms.Select(attrs={'class': 'form-control'}),
            # 'service_buttons': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(MaintenanceForm, self).__init__(*args, **kwargs)
        if not user.has_perm('core.manage_maintenance'):
            self.fields['executive'].queryset = settings.AUTH_USER_MODEL.objects.filter(id=user.id)
            self.fields['executive'].initial = user
            self.fields['executive'].disabled = True

        for field_name, field in self.fields.items():
            if field.widget.attrs.get('class') is None:
                if isinstance(field.widget, (forms.TextInput, forms.Textarea, forms.Select, forms.DateTimeInput)):
                    field.widget.attrs['class'] = 'form-control'
                elif isinstance(field.widget, forms.CheckboxSelectMultiple):
                    field.widget.attrs['class'] = 'form-check-input'
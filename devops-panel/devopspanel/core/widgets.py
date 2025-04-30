from django.forms.widgets import Select
from django.utils.safestring import mark_safe

class TaggableSelectWidget(Select):
    template_name = 'core/widgets/taggable_select.html'

    def __init__(self, attrs=None, choices=()):
        super().__init__(attrs, choices)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        return mark_safe(f'''
            <div class="col-md-4">
                <label class="mb-3" for="{attrs.get('id', name)}">Taggable Select</label>
                {html}
            </div>
        ''')
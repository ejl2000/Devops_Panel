import django
import os
import re

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from devopspanel.core.models import ServiceButton

def clean_tags():
    buttons = ServiceButton.objects.all()
    for button in buttons:
        tags = button.tags.names()
        corrected_tags = []
        for tag in tags:
            cleaned_tag = re.sub(r"[\[\]\'\"]", "", tag)
            split_tags = re.split(r'[,\s]+', cleaned_tag)
            for t in split_tags:
                t = t.strip()
                if t:
                    corrected_tags.append(t)
        if corrected_tags:
            unique_tags = list(set(corrected_tags))
            button.tags.set(unique_tags)
        else:
            button.tags.clear()
        print(f"Cleaned tags for button {button.id}: {unique_tags}")

if __name__ == "__main__":
    clean_tags()

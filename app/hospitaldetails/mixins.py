import nh3
from django.db import models


class NH3CleanSaveMixin:
    """
    Mixin to clean HTML from CharField and TextField fields before saving.

    This ensures that data passed to the frontend is clean and prevents
    admins/editors from accidentally breaking the frontend with unescaped HTML.
    """

    nh3_clean_fields = None
    nh3_tags = set()
    nh3_attributes = {}

    def _iter_nh3_clean_field_names(self):
        if self.nh3_clean_fields is not None:
            return self.nh3_clean_fields
        return [
            field.name
            for field in self._meta.fields
            if isinstance(field, (models.CharField, models.TextField))
        ]

    def save(self, *args, **kwargs):
        for field_name in self._iter_nh3_clean_field_names():
            value = getattr(self, field_name, None)
            if value is None:
                continue
            cleaned = nh3.clean(
                str(value),
                tags=self.nh3_tags,
                attributes=self.nh3_attributes,
            )
            setattr(self, field_name, cleaned)
        return super().save(*args, **kwargs)

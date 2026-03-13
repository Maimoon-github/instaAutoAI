"""
Custom validators for model fields and API input.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.constants import (
    INSTAGRAM_HASHTAG_MIN,
    INSTAGRAM_HASHTAG_MAX,
    INSTAGRAM_CAPTION_MAX_CHARS,
    ALLOWED_ASPECT_RATIOS,
    HASHTAG_REGEX,
)


def validate_hashtag_count(value):
    """
    Validate that a list of hashtags meets min/max requirements.
    """
    if not isinstance(value, (list, tuple)):
        raise ValidationError(_("Hashtags must be a list."))
    if len(value) < INSTAGRAM_HASHTAG_MIN:
        raise ValidationError(
            _("At least %(min)d hashtags are required.") % {"min": INSTAGRAM_HASHTAG_MIN}
        )
    if len(value) > INSTAGRAM_HASHTAG_MAX:
        raise ValidationError(
            _("No more than %(max)d hashtags allowed.") % {"max": INSTAGRAM_HASHTAG_MAX}
        )
    for tag in value:
        if not re.match(HASHTAG_REGEX, tag):
            raise ValidationError(_("Hashtag '%(tag)s' is not valid.") % {"tag": tag})


def validate_aspect_ratio(value):
    """
    Validate that aspect ratio is one of the allowed values.
    """
    if value not in ALLOWED_ASPECT_RATIOS:
        raise ValidationError(
            _("Aspect ratio '%(value)s' is not allowed. Choose from %(choices)s.")
            % {"value": value, "choices": ", ".join(ALLOWED_ASPECT_RATIOS)}
        )


def validate_caption_length(value):
    """
    Validate that a caption does not exceed the Instagram limit.
    """
    if len(value) > INSTAGRAM_CAPTION_MAX_CHARS:
        raise ValidationError(
            _("Caption must not exceed %(max)s characters.")
            % {"max": INSTAGRAM_CAPTION_MAX_CHARS}
        )


def validate_no_hashtags_in_caption(value):
    """
    Ensure the caption body does not contain any '#' characters.
    Hashtags should be stored separately.
    """
    if "#" in value:
        raise ValidationError(_("Caption must not contain '#' characters."))


def validate_json_schema(schema):
    """
    Returns a validator that checks if a JSON value matches the given schema.
    This is a placeholder; in production use `jsonschema` library.
    """
    from jsonschema import validate, ValidationError as JsonSchemaError

    def _validate(value):
        try:
            validate(instance=value, schema=schema)
        except JsonSchemaError as e:
            raise ValidationError(_("Invalid JSON structure: %(error)s") % {"error": str(e)})

    return _validate
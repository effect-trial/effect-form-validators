#!/usr/bin/env python
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from edc_test_settings.default_test_settings import DefaultTestSettings

app_name = "effect_form_validators"
base_dir = Path(__file__).absolute().parent.parent.parent

project_settings = DefaultTestSettings(
    calling_file=__file__,
    BASE_DIR=base_dir,
    APP_NAME=app_name,
    DEBUG=True,
    SUBJECT_CONSENT_MODEL=None,
    INSTALLED_APPS=[
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.sites",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "effect_form_validators.apps.AppConfig",
    ],
    TEMPLATES=[
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
            },
        },
    ],
    WSGI_APPLICATION="effect_form_validators.wsgi.application",
    AUTH_PASSWORD_VALIDATORS=[
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ],
    EDC_PROTOCOL_STUDY_OPEN_DATETIME=datetime(2022, 5, 10, tzinfo=ZoneInfo("Africa/Gaborone")),
    EDC_PROTOCOL_STUDY_CLOSE_DATETIME=datetime(
        2026, 12, 31, tzinfo=ZoneInfo("Africa/Gaborone")
    ),
).settings


for k, v in project_settings.items():
    setattr(sys.modules[__name__], k, v)

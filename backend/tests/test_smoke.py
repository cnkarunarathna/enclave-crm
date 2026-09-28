from django.core.management import call_command


def test_django_system_check_passes():
    # Fails loudly if settings, installed apps or URL config are broken.
    call_command("check")

from django.db import migrations

LEGACY_PROVIDER = "ASP"
CURRENT_PROVIDER = "AGUSTA"


def rename_legacy_provider(apps, schema_editor):
    Enrichment = apps.get_model("enrichments", "Enrichment")
    Enrichment.objects.filter(provider=LEGACY_PROVIDER).update(provider=CURRENT_PROVIDER)


def restore_legacy_provider(apps, schema_editor):
    Enrichment = apps.get_model("enrichments", "Enrichment")
    Enrichment.objects.filter(provider=CURRENT_PROVIDER).update(provider=LEGACY_PROVIDER)


class Migration(migrations.Migration):
    dependencies = [
        ("enrichments", "0003_enrichment_enrichment_created_idx"),
    ]

    operations = [
        migrations.RunPython(rename_legacy_provider, restore_legacy_provider),
    ]

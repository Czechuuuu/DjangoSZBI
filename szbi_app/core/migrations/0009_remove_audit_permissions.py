# Generated manually

from django.db import migrations


def remove_audit_permissions(apps, schema_editor):
    """Usuwa uprawnienia związane z audytami z bazy danych"""
    Permission = apps.get_model('core', 'Permission')
    Permission.objects.filter(category='audits').delete()


def restore_audit_permissions(apps, schema_editor):
    """Przywraca uprawnienia audytów (reverse migration)"""
    Permission = apps.get_model('core', 'Permission')
    
    audit_permissions = [
        ('audits', 'Administrator audytów', 'Przeglądanie wszystkich audytów i zarządzanie właścicielami audytów'),
        ('audits', 'Przeglądający audyty', 'Przeglądanie wszystkich audytów bez możliwości edycji'),
        ('audits', 'Właściciel audytów', 'Dostęp do wszystkich audytów, wypełnianie danych i zmiany statusów'),
        ('audits', 'Menedżer audytów', 'Dostęp do wszystkich audytów i wypełnianie danych bez zmiany statusów'),
    ]
    
    for category, name, description in audit_permissions:
        Permission.objects.update_or_create(
            name=name,
            defaults={
                'category': category,
                'description': description,
                'is_system': True,
            }
        )


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_load_system_permissions'),
    ]

    operations = [
        migrations.RunPython(remove_audit_permissions, restore_audit_permissions),
    ]

from django.apps import AppConfig


class RbiRegistryAppConfig(AppConfig):
    """Django app config for RBI-specific models + endpoints.
    
    Sits alongside indigo_api/ (which we keep unchanged) and hosts
    our custom work: WorkingUnit, UnitMembership, MDOwnership,
    DraftAmendment, and their supporting views.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rbi_registry_app'
    verbose_name = 'RBI Registry (custom)'
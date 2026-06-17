class PeriodicoRouter:
    """
    A router to control all database operations on models.
    Directs Django internal apps to the 'default' connection (which uses search_path=public).
    Directs custom periodico models to the 'periodico_db' connection (which uses search_path=pdg,public).
    Ensures that migrations do not affect the 'periodico_db' alias.
    """
    route_app_labels = {
        'accounts', 'companies', 'authorization', 'plans', 'editions', 
        'files', 'processing', 'purchases', 'payments', 'access_control', 
        'reading', 'incidents', 'notifications', 'audit', 'security', 
        'content', 'seo', 'configuration', 'periodico'
    }

    def db_for_read(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'periodico_db'
        return 'default'

    def db_for_write(self, model, **hints):
        if model._meta.app_label in self.route_app_labels:
            return 'periodico_db'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations within same app label / schema limits
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
            return obj1._meta.app_label == obj2._meta.app_label
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Never run migrations on the periodico_db connection
        if db == 'periodico_db':
            return False
        # Do not run migrations for our custom business apps on the default connection either
        if app_label in self.route_app_labels:
            return False
        # Allow Django internal apps to migrate on the default connection (pointing to public schema)
        return db == 'default'

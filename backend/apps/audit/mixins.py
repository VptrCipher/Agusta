from .context import audit_actor


class AuditActorMixin:
    def perform_create(self, serializer):
        with audit_actor(self.request.user):
            serializer.save()

    def perform_update(self, serializer):
        with audit_actor(self.request.user):
            serializer.save()

    def perform_destroy(self, instance):
        with audit_actor(self.request.user):
            instance.delete()

from rest_framework import serializers

from .models import Enrichment


class EnrichmentSerializer(serializers.ModelSerializer):
    content_type_model = serializers.SerializerMethodField()
    linked_object = serializers.SerializerMethodField()
    linked_object_id = serializers.SerializerMethodField()

    def linked_parent(self, obj):
        for name in ("case", "alert", "artifact"):
            parent = getattr(obj, name, None)
            if parent:
                return name, parent
        return "", None

    def get_content_type_model(self, obj):
        name, _parent = self.linked_parent(obj)
        return name

    def get_linked_object(self, obj):
        name, parent = self.linked_parent(obj)
        if not parent:
            return ""
        readable_id_field = f"{name}_id"
        return getattr(parent, readable_id_field, "") or str(parent.id)

    def get_linked_object_id(self, obj):
        _name, parent = self.linked_parent(obj)
        return str(parent.id) if parent else ""

    def validate(self, attrs):
        parents = [
            attrs.get("case", getattr(self.instance, "case", None)),
            attrs.get("alert", getattr(self.instance, "alert", None)),
            attrs.get("artifact", getattr(self.instance, "artifact", None)),
        ]
        if sum(1 for parent in parents if parent) != 1:
            raise serializers.ValidationError("Exactly one of case, alert, or artifact is required.")
        return attrs

    class Meta:
        model = Enrichment
        fields = "__all__"
        read_only_fields = ("id", "enrichment_id", "created_at", "updated_at")

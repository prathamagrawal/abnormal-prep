from rest_framework import serializers

from files.models import File


class FileSerializer(serializers.ModelSerializer):
    original_file = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = File
        fields = [
            "id",
            "file",
            "original_filename",
            "file_type",
            "size",
            "uploaded_at",
            "user_id",
            "file_hash",
            "reference_count",
            "is_reference",
            "original_file",
        ]
        read_only_fields = fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_reference and instance.original_file_id:
            data["reference_count"] = instance.original_file.reference_count
            data["original_file"] = str(instance.original_file_id)
        elif instance.original_file_id is None:
            data["original_file"] = None
        return data

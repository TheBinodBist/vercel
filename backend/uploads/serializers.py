from rest_framework import serializers


class DeploySerializer(serializers.Serializer):
    repoUrl = serializers.URLField(max_length=500)

    def validate_repoUrl(self, value):
        if not value.lower().startswith("https://"):
            raise serializers.ValidationError("Only https:// repository URLs are allowed.")
        return value

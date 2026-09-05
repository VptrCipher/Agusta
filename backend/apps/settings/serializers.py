import json
import math

from rest_framework import serializers

from .models import (
    CustomVariable,
    LdapConfig,
    LLMProviderConfig,
    RuntimeConfig,
    SiemElkConfig,
    SiemSplunkConfig,
    ThreatIntelAlienVaultOTXConfig,
    ThreatIntelOpenCTIConfig,
)


MAX_CUSTOM_VARIABLE_VALUE_BYTES = 65_536
MAX_CUSTOM_VARIABLE_DEPTH = 20
MAX_SAFE_INTEGER = 9_007_199_254_740_991


def _validate_structured_custom_variable(value, depth=0):
    if isinstance(value, list):
        if depth > MAX_CUSTOM_VARIABLE_DEPTH:
            raise serializers.ValidationError(
                f"Value cannot exceed {MAX_CUSTOM_VARIABLE_DEPTH} levels of nesting."
            )
        for item in value:
            _validate_structured_custom_variable(item, depth + 1)
        return
    if isinstance(value, dict):
        if depth > MAX_CUSTOM_VARIABLE_DEPTH:
            raise serializers.ValidationError(
                f"Value cannot exceed {MAX_CUSTOM_VARIABLE_DEPTH} levels of nesting."
            )
        if any(not isinstance(key, str) for key in value):
            raise serializers.ValidationError("Dictionary keys must be strings.")
        for item in value.values():
            _validate_structured_custom_variable(item, depth + 1)
        return
    if value is None or type(value) in {str, int, float, bool}:
        return
    raise serializers.ValidationError("Value must contain valid JSON values.")


def _validate_custom_variable_value(value_type, value):
    if value_type == CustomVariable.ValueType.STRING:
        if not isinstance(value, str):
            raise serializers.ValidationError("Value must be a string.")
        if value == "":
            raise serializers.ValidationError("Value cannot be empty.")
        encoded_value = value.encode("utf-8")
    elif value_type == CustomVariable.ValueType.INTEGER:
        if type(value) is not int:
            raise serializers.ValidationError("Value must be an integer.")
        if not -MAX_SAFE_INTEGER <= value <= MAX_SAFE_INTEGER:
            raise serializers.ValidationError(
                f"Value must be between {-MAX_SAFE_INTEGER:,} and {MAX_SAFE_INTEGER:,}."
            )
        encoded_value = json.dumps(value).encode("utf-8")
    elif value_type == CustomVariable.ValueType.FLOAT:
        if type(value) not in {int, float}:
            raise serializers.ValidationError("Value must be a number.")
        value = float(value)
        if not math.isfinite(value):
            raise serializers.ValidationError("Value must be a finite number.")
        encoded_value = json.dumps(value).encode("utf-8")
    elif value_type == CustomVariable.ValueType.BOOLEAN:
        if type(value) is not bool:
            raise serializers.ValidationError("Value must be a boolean.")
        encoded_value = json.dumps(value).encode("utf-8")
    elif value_type == CustomVariable.ValueType.LIST:
        if not isinstance(value, list):
            raise serializers.ValidationError("Value must be a list.")
        encoded_value = _encode_structured_custom_variable(value)
    elif value_type == CustomVariable.ValueType.DICTIONARY:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Value must be a dictionary.")
        encoded_value = _encode_structured_custom_variable(value)
    else:
        raise serializers.ValidationError("Unsupported value type.")

    if len(encoded_value) > MAX_CUSTOM_VARIABLE_VALUE_BYTES:
        raise serializers.ValidationError(
            f"Value cannot exceed {MAX_CUSTOM_VARIABLE_VALUE_BYTES:,} UTF-8 bytes."
        )
    return value


def _encode_structured_custom_variable(value):
    _validate_structured_custom_variable(value, depth=1)
    try:
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise serializers.ValidationError("Value must contain valid JSON values.") from exc
    return serialized.encode("utf-8")


class CustomVariableSerializer(serializers.ModelSerializer):
    value = serializers.JSONField(required=False)
    value_configured = serializers.SerializerMethodField()
    confirm_secret_exposure = serializers.BooleanField(write_only=True, required=False, default=False)

    class Meta:
        model = CustomVariable
        fields = (
            "id",
            "key",
            "value_type",
            "value",
            "value_configured",
            "is_secret",
            "description",
            "enabled",
            "created_at",
            "updated_at",
            "confirm_secret_exposure",
        )
        read_only_fields = ("id", "value_configured", "created_at", "updated_at")
        extra_kwargs = {
            "description": {"required": False, "allow_blank": True},
        }

    def get_value_configured(self, obj):
        return obj.value is not None

    def validate_key(self, value):
        if self.instance is not None and value != self.instance.key:
            raise serializers.ValidationError("Key cannot be changed.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        confirmation = attrs.pop("confirm_secret_exposure", False)

        if self.instance is None:
            if "value_type" not in attrs:
                raise serializers.ValidationError({"value_type": "Value type is required."})
            if "value" not in attrs:
                raise serializers.ValidationError({"value": "Value is required."})
        elif attrs.get("value_type", self.instance.value_type) != self.instance.value_type:
            if "value" not in attrs:
                raise serializers.ValidationError({
                    "value": "Value is required when changing the value type."
                })

        value_type = attrs.get(
            "value_type",
            self.instance.value_type if self.instance else None,
        )
        next_is_secret = attrs.get(
            "is_secret",
            self.instance.is_secret if self.instance else False,
        )
        if next_is_secret and value_type != CustomVariable.ValueType.STRING:
            raise serializers.ValidationError({
                "is_secret": "Only String variables can be secret."
            })
        if (
            self.instance is not None
            and self.instance.is_secret
            and not next_is_secret
            and not confirmation
        ):
            raise serializers.ValidationError({
                "confirm_secret_exposure": "Confirm that this secret value may be exposed."
            })

        if "value" in attrs:
            try:
                attrs["value"] = _validate_custom_variable_value(value_type, attrs["value"])
            except serializers.ValidationError as exc:
                raise serializers.ValidationError({"value": exc.detail}) from exc
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.is_secret:
            data["value"] = None
        return data


class LLMProviderConfigSerializer(serializers.ModelSerializer):
    api_key_configured = serializers.SerializerMethodField()

    class Meta:
        model = LLMProviderConfig
        fields = (
            "id",
            "name",
            "base_url",
            "model",
            "api_key",
            "api_key_configured",
            "proxy",
            "tags",
            "enabled",
            "priority",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "api_key_configured", "created_at", "updated_at")
        extra_kwargs = {
            "api_key": {"required": False, "allow_blank": True, "trim_whitespace": False},
            "proxy": {"required": False, "allow_blank": True},
            "tags": {"required": False},
        }

    def get_api_key_configured(self, obj):
        return bool(obj.api_key)

    def validate_tags(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")

        tags = []
        for item in value:
            tag = str(item).strip()
            if tag and tag not in tags:
                tags.append(tag)
        return tags

    def validate(self, attrs):
        attrs = super().validate(attrs)
        tags = attrs.get("tags")
        if tags is None and self.instance is not None:
            tags = self.instance.tags
        if not tags:
            raise serializers.ValidationError({"tags": "Select at least one tag."})
        return attrs

    def validate_proxy(self, value):
        proxy = (value or "").strip()
        if proxy and not proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            raise serializers.ValidationError("Proxy must start with http://, https://, socks4://, or socks5://.")
        return proxy

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["api_key"] = ""
        return data


class ThreatIntelAlienVaultOTXConfigSerializer(serializers.ModelSerializer):
    api_key_configured = serializers.SerializerMethodField()

    class Meta:
        model = ThreatIntelAlienVaultOTXConfig
        fields = (
            "enabled",
            "api_key",
            "api_key_configured",
            "base_url",
            "proxy",
            "updated_at",
        )
        read_only_fields = ("api_key_configured", "updated_at")
        extra_kwargs = {
            "api_key": {"required": True, "allow_blank": False, "trim_whitespace": False},
            "proxy": {"required": False, "allow_blank": True},
        }

    def get_api_key_configured(self, obj):
        return bool(obj.api_key)

    def validate_proxy(self, value):
        proxy = (value or "").strip()
        if proxy and not proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            raise serializers.ValidationError("Proxy must start with http://, https://, socks4://, or socks5://.")
        return proxy

    def validate(self, attrs):
        attrs = super().validate(attrs)
        api_key = attrs.get("api_key")
        if api_key is None and self.instance is not None:
            api_key = self.instance.api_key
        if not str(api_key or "").strip():
            raise serializers.ValidationError({"api_key": "API key is required."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["api_key"] = ""
        return data


class ThreatIntelOpenCTIConfigSerializer(serializers.ModelSerializer):
    token_configured = serializers.SerializerMethodField()

    class Meta:
        model = ThreatIntelOpenCTIConfig
        fields = (
            "enabled",
            "url",
            "token",
            "token_configured",
            "ssl_verify",
            "proxy",
            "updated_at",
        )
        read_only_fields = ("token_configured", "updated_at")
        extra_kwargs = {
            "url": {"required": True, "allow_blank": False},
            "token": {"required": True, "allow_blank": False, "trim_whitespace": False},
            "proxy": {"required": False, "allow_blank": True},
        }

    def get_token_configured(self, obj):
        return bool(obj.token)

    def validate_proxy(self, value):
        proxy = (value or "").strip()
        if proxy and not proxy.startswith(("http://", "https://", "socks4://", "socks5://")):
            raise serializers.ValidationError("Proxy must start with http://, https://, socks4://, or socks5://.")
        return proxy

    def validate(self, attrs):
        attrs = super().validate(attrs)
        token = attrs.get("token")
        if token is None and self.instance is not None:
            token = self.instance.token
        if not str(token or "").strip():
            raise serializers.ValidationError({"token": "API token is required."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["token"] = ""
        return data


class SiemSplunkConfigSerializer(serializers.ModelSerializer):
    password_configured = serializers.SerializerMethodField()

    class Meta:
        model = SiemSplunkConfig
        fields = (
            "host",
            "port",
            "username",
            "password",
            "password_configured",
            "scheme",
            "verify",
            "updated_at",
        )
        read_only_fields = ("password_configured", "updated_at")
        extra_kwargs = {
            "host": {"required": True, "allow_blank": False},
            "username": {"required": True, "allow_blank": False},
            "password": {"required": True, "allow_blank": False, "trim_whitespace": False},
        }

    def get_password_configured(self, obj):
        return bool(obj.password)

    def validate_port(self, value):
        if value <= 0 or value > 65535:
            raise serializers.ValidationError("Port must be between 1 and 65535.")
        return value

    def validate_scheme(self, value):
        scheme = (value or "").strip().lower()
        if scheme not in {"http", "https"}:
            raise serializers.ValidationError("Scheme must be http or https.")
        return scheme

    def validate(self, attrs):
        attrs = super().validate(attrs)
        for field in ("host", "username", "password"):
            value = attrs.get(field)
            if value is None and self.instance is not None:
                value = getattr(self.instance, field)
            if not str(value or "").strip():
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["password"] = ""
        return data


class SiemElkConfigSerializer(serializers.ModelSerializer):
    api_key_configured = serializers.SerializerMethodField()

    class Meta:
        model = SiemElkConfig
        fields = (
            "host",
            "api_key",
            "api_key_configured",
            "verify_certs",
            "process_alert_from_index_enabled",
            "action_index",
            "action_poll_interval_seconds",
            "action_size",
            "updated_at",
        )
        read_only_fields = ("api_key_configured", "updated_at")
        extra_kwargs = {
            "host": {"required": True, "allow_blank": False},
            "api_key": {"required": True, "allow_blank": False, "trim_whitespace": False},
            "action_index": {"required": False, "allow_blank": True},
            "action_poll_interval_seconds": {"required": False, "allow_null": True},
            "action_size": {"required": False, "allow_null": True},
        }

    def get_api_key_configured(self, obj):
        return bool(obj.api_key)

    def validate_action_poll_interval_seconds(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError("Action poll interval must be greater than 0.")
        return value

    def validate_action_size(self, value):
        if value is None:
            return value
        if value <= 0:
            raise serializers.ValidationError("Action size must be greater than 0.")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        for field in ("host", "api_key"):
            value = attrs.get(field)
            if value is None and self.instance is not None:
                value = getattr(self.instance, field)
            if not str(value or "").strip():
                raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required."})
        process_enabled = attrs.get("process_alert_from_index_enabled")
        if process_enabled is None and self.instance is not None:
            process_enabled = self.instance.process_alert_from_index_enabled
        if process_enabled:
            action_index = attrs.get("action_index")
            if action_index is None and self.instance is not None:
                action_index = self.instance.action_index
            if not str(action_index or "").strip():
                raise serializers.ValidationError({"action_index": "Action index is required when alert processing is enabled."})
            poll_interval = attrs.get("action_poll_interval_seconds")
            if "action_poll_interval_seconds" in attrs and poll_interval is None:
                raise serializers.ValidationError({
                    "action_poll_interval_seconds": "Action poll interval is required when alert processing is enabled."
                })
            if poll_interval is None and self.instance is not None:
                poll_interval = self.instance.action_poll_interval_seconds
            if poll_interval is None:
                raise serializers.ValidationError({
                    "action_poll_interval_seconds": "Action poll interval is required when alert processing is enabled."
                })
            action_size = attrs.get("action_size")
            if "action_size" in attrs and action_size is None:
                raise serializers.ValidationError({
                    "action_size": "Action size is required when alert processing is enabled."
                })
            if action_size is None and self.instance is not None:
                action_size = self.instance.action_size
            if action_size is None:
                raise serializers.ValidationError({"action_size": "Action size is required when alert processing is enabled."})
        elif attrs.get("action_poll_interval_seconds") is None:
            attrs.pop("action_poll_interval_seconds", None)
        if not process_enabled and attrs.get("action_size") is None:
            attrs.pop("action_size", None)
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["api_key"] = ""
        return data


class LdapConfigSerializer(serializers.ModelSerializer):
    bind_password_configured = serializers.SerializerMethodField()

    class Meta:
        model = LdapConfig
        fields = (
            "enabled",
            "server_uri",
            "domain",
            "bind_dn",
            "bind_password",
            "bind_password_configured",
            "user_search_base_dn",
            "user_login_attr",
            "updated_at",
        )
        read_only_fields = ("bind_password_configured", "updated_at")
        extra_kwargs = {
            "server_uri": {"required": False, "allow_blank": True},
            "domain": {"required": False, "allow_blank": True},
            "bind_dn": {"required": False, "allow_blank": True},
            "bind_password": {"required": False, "allow_blank": True, "trim_whitespace": False},
            "user_search_base_dn": {"required": False, "allow_blank": True},
            "user_login_attr": {"required": False, "allow_blank": True},
        }

    def get_bind_password_configured(self, obj):
        return bool(obj.bind_password)

    def validate_server_uri(self, value):
        server_uri = (value or "").strip()
        if server_uri and not server_uri.startswith(("ldap://", "ldaps://")):
            raise serializers.ValidationError("Server URI must start with ldap:// or ldaps://.")
        return server_uri

    def validate(self, attrs):
        attrs = super().validate(attrs)
        enabled = attrs.get("enabled")
        if enabled is None and self.instance is not None:
            enabled = self.instance.enabled

        server_uri = attrs.get("server_uri")
        if server_uri is None and self.instance is not None:
            server_uri = self.instance.server_uri
        if enabled and not str(server_uri or "").strip():
            raise serializers.ValidationError({"server_uri": "Server URI is required when LDAP is enabled."})

        bind_dn = attrs.get("bind_dn")
        if bind_dn is None and self.instance is not None:
            bind_dn = self.instance.bind_dn
        bind_password = attrs.get("bind_password")
        if bind_password is None and self.instance is not None:
            bind_password = self.instance.bind_password
        if str(bind_dn or "").strip() and not str(bind_password or "").strip():
            raise serializers.ValidationError({"bind_password": "Bind password is required when bind DN is configured."})

        user_login_attr = attrs.get("user_login_attr")
        if user_login_attr is None and self.instance is not None:
            user_login_attr = self.instance.user_login_attr
        if not str(user_login_attr or "").strip():
            raise serializers.ValidationError({"user_login_attr": "User login attribute is required."})
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not self.context.get("reveal_secrets"):
            data["bind_password"] = ""
        return data


class RuntimeConfigSerializer(serializers.ModelSerializer):
    DASHBOARD_REFRESH_INTERVALS = {300, 900, 1800, 3600}

    class Meta:
        model = RuntimeConfig
        fields = (
            "prompt_language",
            "stream_maxlen",
            "dashboard_refresh_interval_seconds",
            "updated_at",
        )
        read_only_fields = ("updated_at",)

    def validate_prompt_language(self, value):
        language = (value or "").strip().lower()
        if language not in {"en", "zh"}:
            raise serializers.ValidationError("Prompt language must be en or zh.")
        return language

    def validate_stream_maxlen(self, value):
        if value <= 0:
            raise serializers.ValidationError("Stream maxlen must be greater than 0.")
        return value

    def validate_dashboard_refresh_interval_seconds(self, value):
        if value not in self.DASHBOARD_REFRESH_INTERVALS:
            raise serializers.ValidationError("Dashboard refresh interval must be 300, 900, 1800, or 3600 seconds.")
        return value

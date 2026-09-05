import httpx
from langchain_openai import ChatOpenAI

from apps.settings.runtime_config import get_llm_configs


def _http_client_kwargs(config):
    if "proxy" not in config:
        return {}

    proxy = (config.get("proxy") or "").strip()
    client_kwargs = {"trust_env": False}
    if proxy:
        client_kwargs["proxy"] = proxy
    return {
        "http_client": httpx.Client(**client_kwargs),
        "http_async_client": httpx.AsyncClient(**client_kwargs),
        "http_socket_options": (),
    }


class LLMAPI:
    def __init__(self, *, temperature=0.0, configs=None):
        self.temperature = temperature
        self.configs = get_llm_configs() if configs is None else configs
        if not isinstance(self.configs, list):
            raise ValueError("LLM provider configurations must be a list.")
        if not self.configs:
            raise ValueError("No enabled LLM provider configurations found.")

    def select_config(self, tag=None):
        if tag is None:
            return self.configs[0]

        required_tags = {tag} if isinstance(tag, str) else set(tag)
        for config in self.configs:
            config_tags = set(config.get("tags", []))
            if required_tags.issubset(config_tags):
                return config

        raise ValueError(f"No LLM configuration found matching tag(s): {tag}")

    def get_model(self, tag=None, **kwargs):
        config = self.select_config(tag=tag)
        params = {
            "temperature": self.temperature,
            "model": config.get("model"),
            "base_url": config.get("base_url"),
            "api_key": config.get("api_key"),
            **_http_client_kwargs(config),
        }
        params.update(kwargs)
        return ChatOpenAI(**params)

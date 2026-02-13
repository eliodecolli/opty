import pytest

from opty.core import load_config


class TestLoadConfig:
    def test_returns_config_dict(self, tmp_path):
        config_file = tmp_path / "opty.config.yaml"
        config_file.write_text("config:\n  builder:\n    type: gemini\n")
        result = load_config(config_file)
        assert result == {"builder": {"type": "gemini"}}

    def test_missing_config_key_returns_empty_dict(self, tmp_path):
        config_file = tmp_path / "opty.config.yaml"
        config_file.write_text("other: value\n")
        assert load_config(config_file) == {}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

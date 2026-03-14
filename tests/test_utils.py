"""Test utility functions."""

import tempfile
from pathlib import Path

import pytest

from statebind.utils.config import load_config
from statebind.utils.io import ensure_dir, save_json, load_json


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "test.yaml"
    config_file.write_text("key: value\nnested:\n  a: 1\n")
    config = load_config(config_file)
    assert config["key"] == "value"
    assert config["nested"]["a"] == 1


def test_load_config_missing():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path.yaml")


def test_load_config_empty(tmp_path):
    config_file = tmp_path / "empty.yaml"
    config_file.write_text("")
    config = load_config(config_file)
    assert config == {}


def test_ensure_dir(tmp_path):
    new_dir = tmp_path / "a" / "b" / "c"
    result = ensure_dir(new_dir)
    assert new_dir.is_dir()
    assert result == new_dir


def test_save_and_load_json(tmp_path):
    data = {"key": "value", "numbers": [1, 2, 3]}
    json_path = tmp_path / "test.json"
    save_json(data, json_path)
    loaded = load_json(json_path)
    assert loaded == data

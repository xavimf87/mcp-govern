"""Tests per al mòdul datasets.py — validació de la configuració."""

from __future__ import annotations

from mcp_govern.datasets import BASE_URL, DATASETS, dataset_url


class TestDatasets:
    def test_all_datasets_have_required_keys(self):
        for key, ds in DATASETS.items():
            assert "id" in ds, f"Dataset '{key}' no té 'id'"
            assert "nom" in ds, f"Dataset '{key}' no té 'nom'"
            assert "camps" in ds, f"Dataset '{key}' no té 'camps'"

    def test_all_ids_are_strings(self):
        for key, ds in DATASETS.items():
            assert isinstance(ds["id"], str), f"Dataset '{key}' id no és string"
            assert len(ds["id"]) > 0, f"Dataset '{key}' id és buit"

    def test_all_ids_are_unique(self):
        ids = [ds["id"] for ds in DATASETS.values()]
        assert len(ids) == len(set(ids)), "Hi ha IDs duplicats"

    def test_all_keys_are_snake_case(self):
        import re

        for key in DATASETS:
            assert re.match(r"^[a-z][a-z0-9_]*$", key), f"Key '{key}' no és snake_case"

    def test_camps_is_list(self):
        for key, ds in DATASETS.items():
            assert isinstance(ds["camps"], list), f"Dataset '{key}' camps no és llista"

    def test_dataset_url(self):
        url = dataset_url("contractes")
        ds_id = DATASETS["contractes"]["id"]
        assert url == f"{BASE_URL}/{ds_id}.json"

    def test_dataset_url_invalid_key_raises(self):
        import pytest

        with pytest.raises(KeyError):
            dataset_url("no_existeix")

    def test_known_datasets_exist(self):
        expected = [
            "contractes",
            "pscp",
            "subvencions",
            "convocatories",
            "contractes_menors",
            "retrib_alts_carrecs",
            "retrib_directius_sector_public",
            "pressupostos",
            "rlt_funcionaris",
            "agenda_lobbies",
            "viatges_alts_carrecs",
        ]
        for name in expected:
            assert name in DATASETS, f"Dataset esperat '{name}' no trobat"

    def test_datasets_with_camps_have_valid_entries(self):
        for key, ds in DATASETS.items():
            for camp in ds["camps"]:
                assert isinstance(camp, str), f"Camp '{camp}' en '{key}' no és string"
                assert len(camp) > 0, f"Camp buit en '{key}'"

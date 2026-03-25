"""Tests per les funcions helper de server.py (_fmt, _build_where, _normalize_accents, _fix_import_centims)."""

from __future__ import annotations

from mcp_govern.server import (
    _build_where,
    _filter_relevant,
    _fix_import_centims,
    _fmt,
    _normalize_accents,
    _normalize_tipus_contracte,
)

# ---------------------------------------------------------------------------
# _fmt
# ---------------------------------------------------------------------------


class TestFmt:
    def test_empty_records(self):
        assert _fmt([]) == "No s'han trobat resultats."

    def test_records_without_total(self):
        result = _fmt([{"a": 1}])
        assert '"a": 1' in result
        assert "Mostrant" not in result

    def test_records_with_total_exact(self):
        result = _fmt([{"a": 1}], total=1)
        assert "Total: 1 resultats." in result

    def test_records_with_total_more(self):
        result = _fmt([{"a": 1}], total=100)
        assert "Mostrant 1-1 de 100 resultats totals" in result
        assert "99 resultats més" in result

    def test_records_with_offset(self):
        result = _fmt([{"a": 1}, {"b": 2}], total=50, offset=10)
        assert "Mostrant 11-12 de 50 resultats totals" in result

    def test_records_with_custom_limit(self):
        result = _fmt([{"a": 1}], total=1, limit=10)
        assert "Total: 1 resultats." in result


# ---------------------------------------------------------------------------
# _build_where
# ---------------------------------------------------------------------------


class TestBuildWhere:
    def test_empty_clauses(self):
        assert _build_where([]) is None

    def test_single_clause(self):
        assert _build_where(["exercici='2024'"]) == "exercici='2024'"

    def test_multiple_clauses(self):
        result = _build_where(["exercici='2024'", "tipus='SERVEIS'"])
        assert result == "exercici='2024' AND tipus='SERVEIS'"

    def test_filters_none_and_empty(self):
        result = _build_where([None, "", "exercici='2024'", None])
        assert result == "exercici='2024'"

    def test_all_empty(self):
        assert _build_where([None, "", ""]) is None


# ---------------------------------------------------------------------------
# _normalize_accents
# ---------------------------------------------------------------------------


class TestNormalizeAccents:
    def test_plain_text_unchanged(self):
        """Plain text without accents should remain unchanged."""
        assert _normalize_accents("test") == "test"

    def test_plain_vowels_unchanged(self):
        """Plain vowels (no accents) should NOT be replaced."""
        assert _normalize_accents("aeiou") == "aeiou"

    def test_accenture_unchanged(self):
        """'Accenture' should remain unchanged (no accented chars)."""
        assert _normalize_accents("Accenture") == "Accenture"

    def test_accented_vowels_replaced(self):
        """Accented vowels should be replaced with %."""
        assert _normalize_accents("àèíòú") == "%%%%%"

    def test_accented_catalan(self):
        """Catalan accented words should only replace accented chars."""
        result = _normalize_accents("educació")
        assert result == "educaci%"

    def test_uppercase_accents(self):
        result = _normalize_accents("ÀÉÏÜ")
        assert result == "%%%%"

    def test_no_vowels(self):
        assert _normalize_accents("brcs") == "brcs"

    def test_mixed_accented_and_plain(self):
        """Only accented vowels get replaced, plain vowels stay."""
        result = _normalize_accents("Generalitat")
        assert result == "Generalitat"  # no accents, no changes

    def test_mixed_with_accent(self):
        result = _normalize_accents("Départàment")
        assert "D" in result
        assert "%" in result
        # 'é' and 'à' should become %, plain 'a' stays
        assert result == "D%part%ment"


# ---------------------------------------------------------------------------
# _fix_import_centims
# ---------------------------------------------------------------------------


class TestFixImportCentims:
    def test_converts_centims(self):
        records = [{"import": "1500000"}]
        result = _fix_import_centims(records, "import")
        assert result[0]["import"] == "15000.0"

    def test_none_value(self):
        records = [{"import": None}]
        result = _fix_import_centims(records, "import")
        assert result[0]["import"] is None

    def test_missing_field(self):
        records = [{"other": "123"}]
        result = _fix_import_centims(records, "import")
        assert "import" not in result[0]

    def test_invalid_value(self):
        records = [{"import": "not_a_number"}]
        result = _fix_import_centims(records, "import")
        assert result[0]["import"] == "not_a_number"

    def test_multiple_records(self):
        records = [{"import": "100"}, {"import": "200"}]
        result = _fix_import_centims(records, "import")
        assert result[0]["import"] == "1.0"
        assert result[1]["import"] == "2.0"


# ---------------------------------------------------------------------------
# _filter_relevant
# ---------------------------------------------------------------------------


class TestFilterRelevant:
    def test_filters_matching_records(self):
        records = [
            {"nom": "ACCENTURE SL", "import": "1000"},
            {"nom": "RANDOM COMPANY", "import": "2000"},
        ]
        result = _filter_relevant(records, "Accenture")
        assert len(result) == 1
        assert result[0]["nom"] == "ACCENTURE SL"

    def test_case_insensitive(self):
        records = [{"nom": "accenture sl"}]
        result = _filter_relevant(records, "ACCENTURE")
        assert len(result) == 1

    def test_no_match(self):
        records = [{"nom": "TELEFONICA"}]
        result = _filter_relevant(records, "Accenture")
        assert len(result) == 0

    def test_empty_records(self):
        assert _filter_relevant([], "test") == []

    def test_match_in_any_field(self):
        records = [{"nom": "OTHER", "descripcio": "Contracte amb Accenture SL"}]
        result = _filter_relevant(records, "Accenture")
        assert len(result) == 1

    def test_non_string_values_ignored(self):
        records = [{"nom": "TEST", "valor": 12345}]
        result = _filter_relevant(records, "TEST")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# _normalize_tipus_contracte
# ---------------------------------------------------------------------------


class TestNormalizeTipusContracte:
    def test_merges_duplicates(self):
        records = [
            {"tipus_contracte": "5. SERVEIS", "total": "100"},
            {"tipus_contracte": "SERVEIS", "total": "20"},
        ]
        result = _normalize_tipus_contracte(records)
        assert len(result) == 1
        assert result[0]["tipus_contracte"] == "5. SERVEIS"
        assert result[0]["total"] == "120"

    def test_no_duplicates(self):
        records = [
            {"tipus_contracte": "5. SERVEIS", "total": "100"},
            {"tipus_contracte": "1. OBRES", "total": "50"},
        ]
        result = _normalize_tipus_contracte(records)
        assert len(result) == 2

    def test_empty_records(self):
        assert _normalize_tipus_contracte([]) == []

    def test_sorted_by_total_desc(self):
        records = [
            {"tipus_contracte": "1. OBRES", "total": "50"},
            {"tipus_contracte": "5. SERVEIS", "total": "100"},
        ]
        result = _normalize_tipus_contracte(records)
        assert result[0]["tipus_contracte"] == "5. SERVEIS"
        assert result[1]["tipus_contracte"] == "1. OBRES"

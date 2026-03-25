"""Fixtures compartides per tots els tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def socrata_records():
    """Registres de mostra estil Socrata."""
    return [
        {
            "exercici": "2024",
            "adjudicatari": "EMPRESA TEST SL",
            "organisme_contractant": "Departament de Salut",
            "import_adjudicacio": "150000",
            "tipus_contracte": "5. SERVEIS",
            "codi_expedient": "EXP-001",
        },
        {
            "exercici": "2024",
            "adjudicatari": "ACME CORP SA",
            "organisme_contractant": "Departament d'Educació",
            "import_adjudicacio": "250000",
            "tipus_contracte": "3. SUBMINISTRAMENTS",
            "codi_expedient": "EXP-002",
        },
    ]


@pytest.fixture
def contractes_menors_records():
    """Registres de contractes menors (imports en cèntims)."""
    return [
        {
            "empresa_adjudicat_ria": "EMPRESA TEST SL",
            "import_adjudicat_sense_iva": "1200000",  # 12000.00 €
            "departament_d_adscripci": "Departament de Salut",
            "any": "2024",
            "objecte_del_contracte": "Servei de neteja",
        },
        {
            "empresa_adjudicat_ria": "EMPRESA TEST SL",
            "import_adjudicat_sense_iva": "1100000",  # 11000.00 €
            "departament_d_adscripci": "Departament de Salut",
            "any": "2024",
            "objecte_del_contracte": "Servei de manteniment",
        },
    ]

from datetime import date

import pytest
from worker.workflows.veille_radiologie import (
    WORKFLOW_NAME,
    VeilleInput,
    consigne_periode,
    fenetre_semaine,
)


def test_fenetre_semaine_couvre_sept_jours() -> None:
    now = date(2026, 2, 11)
    debut, libelle = fenetre_semaine(now)
    assert debut == date(2026, 2, 4)
    assert "2026-02-04" in libelle and "2026-02-11" in libelle


def test_consigne_periode_integre_focus_et_sources() -> None:
    consigne = consigne_periode("semaine du 2026-02-04 au 2026-02-11", focus="IRM bas champ", max_sources=8)
    assert "IRM bas champ" in consigne
    assert "8" in consigne
    assert "Sources" in consigne


def test_consigne_periode_sans_focus() -> None:
    consigne = consigne_periode("semaine test", focus="", max_sources=12)
    assert "Point focus spécifique" not in consigne


def test_input_defauts_et_validation() -> None:
    params = VeilleInput()
    assert params.focus == ""
    assert params.max_sources == 12
    with pytest.raises(ValueError):
        VeilleInput(max_sources=2)


def test_workflow_name_stable() -> None:
    assert WORKFLOW_NAME == "veille_radiologie_workflow"

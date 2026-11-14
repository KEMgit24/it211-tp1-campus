"""Partie B : règles de priorité."""

import pytest

from tp1.priorites import Priorite, PrioriteChronologique, PrioriteMerite

from conftest import candidat


def test_priorite_est_abstraite():
    with pytest.raises(TypeError):
        Priorite()


def test_merite_moyenne_decroissante(registre):
    a = candidat(registre, "IPN-2024-0073", moyenne="11.49", credits=14)
    b = candidat(registre, "IPN-2024-0092", moyenne="17.88", credits=18)
    assert PrioriteMerite().ordonner([a, b]) == [b, a]


def test_merite_departage_par_credits_puis_date(registre):
    a = candidat(
        registre, "IPN-2024-0073", "13/01/2026 08:00", moyenne="12", credits=14
    )
    b = candidat(
        registre, "IPN-2024-0056", "12/01/2026 08:00", moyenne="12", credits=18
    )
    c = candidat(
        registre, "IPN-2024-0057", "12/01/2026 07:00", moyenne="12", credits=14
    )
    assert PrioriteMerite().ordonner([a, b, c]) == [b, c, a]


def test_chronologique(registre):
    a = candidat(registre, "IPN-2024-0073", "13/01/2026 08:00")
    b = candidat(registre, "IPN-2024-0056", "12/01/2026 08:00")
    assert PrioriteChronologique().ordonner([a, b]) == [b, a]


def test_ordonner_ne_modifie_pas_la_liste(registre):
    a = candidat(registre, "IPN-2024-0073", "13/01/2026 08:00")
    b = candidat(registre, "IPN-2024-0056", "12/01/2026 08:00")
    liste = [a, b]
    PrioriteChronologique().ordonner(liste)
    assert liste == [a, b]

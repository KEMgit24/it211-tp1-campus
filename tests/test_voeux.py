"""Partie A : lecture des vœux."""

from datetime import datetime

import pytest

from tp1.erreurs import VoeuInvalide
from tp1.voeux import Voeu, lire_horodatage, lire_voeux, normaliser_code

from conftest import CODES, DONNEES, voeu


def test_normaliser_code():
    assert normaliser_code("  opt   282 ") == "OPT 282"
    assert normaliser_code("OPT 281") == "OPT 281"


def test_lire_horodatage():
    assert lire_horodatage("13/01/2026 08:16") == datetime(2026, 1, 13, 8, 16)


@pytest.mark.parametrize(
    "texte", ["31/02/2026 10:15", "2026-01-13 08:16", "13/01/2026", ""]
)
def test_lire_horodatage_refuse(texte):
    with pytest.raises(VoeuInvalide):
        lire_horodatage(texte)


def test_voeu_valide_et_rang():
    v = voeu("IPN-2024-0073", "13/01/2026 08:16", "OPT 282", "OPT 281")
    assert v.rang("OPT 281") == 2
    assert v.rang("OPT 283") is None


@pytest.mark.parametrize(
    "matricule, choix",
    [
        ("ipn-2024-0073", ("OPT 281",)),  # matricule non normalisé
        ("IPN-2024-0073", ()),  # aucun choix
        ("IPN-2024-0073", ("OPT 281", "OPT 281")),  # doublon
        ("IPN-2024-0073", ("OPT 281", "OPT 282", "OPT 283", "OPT 284")),
    ],
)
def test_voeu_invalide(matricule, choix):
    with pytest.raises(VoeuInvalide):
        Voeu(matricule, datetime(2026, 1, 13), choix, 2)


def test_voeu_est_fige():
    v = voeu("IPN-2024-0073", "13/01/2026 08:16", "OPT 282")
    with pytest.raises(AttributeError):  # FrozenInstanceError en dérive
        v.choix = ("OPT 281",)


def test_fichier_fourni():
    voeux, journal = lire_voeux(DONNEES / "voeux_brut.csv", CODES)
    assert len(voeux) == 42
    assert len(journal) == 8
    assert [v.ligne for v in voeux] == sorted(v.ligne for v in voeux)


def test_ligne_correcte(fichier_voeux):
    chemin = fichier_voeux("IPN-2024-0073;13/01/2026 08:16;OPT 282;OPT 281;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert voeux == [
        voeu("IPN-2024-0073", "13/01/2026 08:16", "OPT 282", "OPT 281")
    ]
    assert journal == []


def test_matricule_corrige(fichier_voeux):
    chemin = fichier_voeux(" ipn-2024-0073 ;13/01/2026 08:16;OPT 282;;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert voeux[0].matricule == "IPN-2024-0073"
    assert [(s.ligne, s.gravite) for s in journal] == [(2, "correction")]


def test_horodatage_invalide_rejette_la_ligne(fichier_voeux):
    chemin = fichier_voeux("IPN-2024-0073;31/02/2026 08:16;OPT 282;;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert voeux == []
    assert [(s.ligne, s.gravite) for s in journal] == [(2, "erreur")]


def test_code_inconnu_ignore(fichier_voeux):
    chemin = fichier_voeux("IPN-2024-0073;13/01/2026 08:16;OPT 284;OPT 281;")
    voeux, journal = lire_voeux(chemin, CODES)
    assert voeux[0].choix == ("OPT 281",)
    assert journal[0].gravite == "erreur" and "OPT 284" in journal[0].message


def test_double_soumission(fichier_voeux):
    chemin = fichier_voeux(
        "IPN-2024-0073;13/01/2026 08:16;OPT 282;;",
        "IPN-2024-0056;13/01/2026 09:00;OPT 283;;",
        "IPN-2024-0073;14/01/2026 10:00;OPT 281;OPT 282;",
    )
    voeux, journal = lire_voeux(chemin, CODES)
    assert [v.ligne for v in voeux] == [3, 4]
    assert voeux[1].choix == ("OPT 281", "OPT 282")
    assert [(s.ligne, s.gravite) for s in journal] == [(2, "correction")]


def test_entete_inattendu(fichier_voeux):
    chemin = fichier_voeux(
        "IPN-2024-0073;13/01/2026 08:16;OPT 282;;", entete="Matricule;Date;Choix"
    )
    with pytest.raises(VoeuInvalide):
        lire_voeux(chemin, CODES)

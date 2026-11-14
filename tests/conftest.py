"""Fixtures communes aux tests du TP1 (fichier fourni)."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from campus import Scolarite
from tp1.campagne import Campagne, Candidat, lire_options
from tp1.voeux import ENTETE, Voeu

RACINE = Path(__file__).resolve().parent.parent
DONNEES = RACINE / "donnees"
CODES = {"OPT 281", "OPT 282", "OPT 283"}


@pytest.fixture
def registre():
    """Un registre neuf pour chaque test : une campagne y inscrit des étudiants."""
    return Scolarite.depuis_csv(DONNEES)


@pytest.fixture
def options():
    return lire_options(DONNEES / "ues_optionnelles.csv")


@pytest.fixture
def fichier_voeux(tmp_path):
    """Fabrique un fichier de vœux au format du formulaire, ligne à ligne."""

    def fabriquer(*lignes: str, entete: str = ";".join(ENTETE)) -> Path:
        chemin = tmp_path / "voeux.csv"
        contenu = "\r\n".join([entete, *lignes]) + "\r\n"
        chemin.write_text(contenu, encoding="utf-8-sig", newline="")
        return chemin

    return fabriquer


def voeu(matricule, quand="12/01/2026 08:00", *choix, ligne=2):
    """Un Voeu construit directement, sans passer par un fichier."""
    return Voeu(
        matricule, datetime.strptime(quand, "%d/%m/%Y %H:%M"), tuple(choix), ligne
    )


def candidat(
    registre,
    matricule,
    quand="12/01/2026 08:00",
    *choix,
    moyenne=None,
    credits=None
):
    """Un Candidat ; moyenne et crédits forçables pour tester les départages."""
    releve = registre.releve(matricule, 1)
    return Candidat(
        registre.etudiant(matricule),
        voeu(matricule, quand, *(choix or ("OPT 281",))),
        Decimal(moyenne) if moyenne is not None else releve.moyenne,
        credits if credits is not None else releve.credits_acquis,
    )

"""Campagne d'affectation : chaque candidat, dans l'ordre de priorité, reçoit
la première option de sa liste qui l'accepte encore (dictature sérielle).

Partie B du TP1. Sont FOURNIS : lire_options, Candidat, Decision, les champs de
Resultat, le constructeur et les propriétés options et codes de Campagne.
Les méthodes qui lèvent NotImplementedError sont à écrire ; vous pouvez ajouter
des méthodes auxiliaires (nom commençant par un tiret bas).
"""

import csv
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from campus import ErreurCampus, Etudiant, InscriptionRefusee, Scolarite, UE

from .erreurs import CampagneDejaExecutee, VoeuInvalide
from .priorites import Priorite
from .voeux import Signalement, Voeu

NIVEAU_CAMPAGNE = "L2"
SEMESTRE_CAMPAGNE = 2


def lire_options(chemin: Path | str) -> list[UE]:
    """Lit ues_optionnelles.csv : des UE de L2, semestre 2, ouvertes à toutes
    les filières."""
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    options = []
    for ligne in lignes:
        prerequis = {p.strip() for p in ligne["prerequis"].split("|") if p.strip()}
        options.append(
            UE(
                ligne["code"],
                ligne["intitule"],
                int(ligne["credits"]),
                NIVEAU_CAMPAGNE,
                SEMESTRE_CAMPAGNE,
                capacite=int(ligne["capacite"]),
                prerequis=prerequis,
            )
        )
    if not options:
        raise VoeuInvalide(f"aucune option dans {chemin}")
    return options


@dataclass(frozen=True)
class Candidat:
    """Un étudiant admis à concourir, avec ce qui sert à le classer."""

    etudiant: Etudiant
    voeu: Voeu
    moyenne: Decimal
    credits_acquis: int

    @property
    def matricule(self) -> str:
        return self.etudiant.matricule


@dataclass(frozen=True)
class Decision:
    """Le sort d'un candidat. refus donne, pour chaque choix écarté, ses motifs."""

    rang: int
    matricule: str
    option: str | None
    rang_choix: int | None
    refus: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def affecte(self) -> bool:
        return self.option is not None


@dataclass(frozen=True)
class Resultat:
    """Ce que produit une campagne : décisions dans l'ordre de passage, journal."""

    priorite: str
    options: tuple[UE, ...]
    decisions: tuple[Decision, ...]
    journal: tuple[Signalement, ...]

    def decision(self, matricule: str) -> Decision:
        """Question B.2. La décision du matricule (normalisé : espaces,
        majuscules) ; lève KeyError s'il n'a pas concouru."""
        raise NotImplementedError("question B.2")

    def affectes(self, code: str) -> list[str]:
        """Question B.2. Matricules affectés à l'option, dans l'ordre de passage."""
        raise NotImplementedError("question B.2")

    def non_affectes(self) -> list[str]:
        """Question B.2. Candidats sans option, dans l'ordre de passage."""
        raise NotImplementedError("question B.2")

    def effectifs(self) -> dict[str, int]:
        """Question B.2. {code: nombre d'affectés}, dans l'ordre des options."""
        raise NotImplementedError("question B.2")

    def satisfaction(self) -> Counter:
        """Question B.2. Counter : nombre de candidats par rang de choix obtenu
        (clé None : non affecté)."""
        raise NotImplementedError("question B.2")

    @property
    def erreurs(self) -> list[Signalement]:
        """Question B.2. Les signalements « erreur », dans l'ordre du journal."""
        raise NotImplementedError("question B.2")


class Campagne:
    """Affecte les candidats aux options en inscrivant les étudiants au registre.

    Le constructeur ajoute au registre les options qui n'y sont pas encore :
    l'inscription d'un candidat passe ensuite par registre.inscrire, qui applique
    les règles RG09 et RG10 (capacité, prérequis, crédits) de la séance 2.
    """

    def __init__(
        self, registre: Scolarite, options: list[UE], priorite: Priorite
    ) -> None:
        if not options:
            raise ValueError("une campagne demande au moins une option")
        self.registre = registre
        self.priorite = priorite
        self._options: dict[str, UE] = {}
        for ue in options:
            if ue not in self.registre:
                self.registre.ajouter_ue(ue)
            self._options[ue.code] = self.registre.ue(ue.code)
        self._executee = False

    @property
    def options(self) -> tuple[UE, ...]:
        return tuple(self._options.values())

    @property
    def codes(self) -> set[str]:
        return set(self._options)

    def places_restantes(self, code: str) -> int:
        """Question B.3. Capacité de l'option moins ses inscrits au registre."""
        raise NotImplementedError("question B.3")

    def candidats(
        self, voeux: list[Voeu]
    ) -> tuple[list[Candidat], list[Signalement]]:
        """Question B.3. Écarte (avec un signalement « erreur » à la ligne du vœu)
        les vœux d'étudiants inconnus du registre, sans relevé du semestre 1
        (registre.releve lève ErreurCampus), archivés, ou d'un autre niveau que
        NIVEAU_CAMPAGNE ;
        construit un Candidat pour chacun des autres (moyenne et crédits acquis
        du relevé du semestre 1). Renvoie (candidats, journal)."""
        raise NotImplementedError("question B.3")

    def executer(
        self, voeux: list[Voeu], journal_lecture: list[Signalement] = ()
    ) -> Resultat:
        """Question B.4. Lance la campagne selon l'algorithme de l'énoncé ;
        lève CampagneDejaExecutee au second appel."""
        raise NotImplementedError("question B.4")

    def _traiter(self, rang: int, candidat: Candidat) -> Decision:
        """Question B.4 (auxiliaire suggérée, libre). Décision pour un candidat."""
        raise NotImplementedError("question B.4")

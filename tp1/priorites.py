"""Règles de priorité entre candidats, stratégies interchangeables (partie B)."""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # import réservé aux annotations : évite un import circulaire
    from .campagne import Candidat


class Priorite(ABC):
    """Une règle de priorité : la clé de tri d'un candidat ; la plus petite passe
    d'abord.

    FOURNI, sauf ordonner (question B.1).
    """

    nom: str = ""

    @abstractmethod
    def cle(self, candidat: "Candidat") -> tuple:
        """Clé de tri ; deux candidats distincts ont des clés distinctes."""

    def ordonner(self, candidats: list["Candidat"]) -> list["Candidat"]:
        """Question B.1. Les candidats, du plus prioritaire au moins prioritaire,
        dans une nouvelle liste (la liste reçue n'est pas modifiée)."""
        return sorted(candidats, key=self.cle)

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class PrioriteMerite(Priorite):
    """Moyenne du semestre 1 décroissante, puis crédits acquis décroissants,
    puis dépôt le plus ancien, puis matricule."""

    nom = "merite"

    def cle(self, candidat: "Candidat") -> tuple:
        """Question B.1."""
        return (
            -candidat.moyenne,
            -candidat.credits_acquis,
            candidat.voeu.horodatage,
            candidat.matricule,
        )


class PrioriteChronologique(Priorite):
    """Premier arrivé, premier servi ; le matricule départage les ex aequo."""

    nom = "chronologique"

    def cle(self, candidat: "Candidat") -> tuple:
        """Question B.1."""
        return (candidat.voeu.horodatage, candidat.matricule)


class PrioriteTirage(Priorite):
    """BONUS. Tirage au sort reproductible : la même graine donne toujours le même
    ordre, quel que soit l'ordre dans lequel les candidats sont présentés."""

    nom = "tirage"

    def __init__(self, graine: int = 2026) -> None:
        self.graine = graine

    def cle(self, candidat: "Candidat") -> tuple:
        """Bonus."""
        generateur = random.Random(f"{self.graine}:{candidat.matricule}")
        return (generateur.random(), candidat.matricule)

    def __repr__(self) -> str:
        return f"PrioriteTirage(graine={self.graine})"


# FOURNI
PRIORITES: dict[str, type[Priorite]] = {
    PrioriteMerite.nom: PrioriteMerite,
    PrioriteChronologique.nom: PrioriteChronologique,
    PrioriteTirage.nom: PrioriteTirage,
}

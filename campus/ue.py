"""Unité d'enseignement (UE), écrite comme une dataclass validée à la construction."""

import re
from dataclasses import dataclass, field
from typing import ClassVar

from .erreurs import DonneeInvalide
from .personnes import Enseignant, Etudiant


@dataclass(eq=False)
class UE:
    """Une UE du catalogue (RG02). filiere vide = tronc commun."""

    code: str
    intitule: str
    credits: int
    niveau: str
    semestre: int
    filiere: str = ""
    capacite: int = 60
    responsable: Enseignant | None = None
    prerequis: set[str] = field(default_factory=set)

    MOTIF_CODE: ClassVar[re.Pattern] = re.compile(r"[A-Z]{2,3} \d{3}")

    def __post_init__(self) -> None:
        self.code = " ".join(str(self.code).split()).upper()
        if not self.MOTIF_CODE.fullmatch(self.code):
            raise DonneeInvalide(
                "code",
                self.code,
                "deux ou trois lettres, une espace, trois chiffres",
            )
        if not self.intitule.strip():
            raise DonneeInvalide("intitule", self.intitule, "obligatoire")
        if type(self.credits) is not int or not 1 <= self.credits <= 12:
            raise DonneeInvalide("credits", self.credits, "entier de 1 à 12")
        if self.niveau not in Etudiant.NIVEAUX:
            raise DonneeInvalide("niveau", self.niveau, "L1, L2 ou L3")
        if self.semestre not in (1, 2):
            raise DonneeInvalide("semestre", self.semestre, "1 ou 2")
        if self.filiere not in ("", *Etudiant.FILIERES):
            raise DonneeInvalide("filiere", self.filiere, "vide ou filière connue")
        if type(self.capacite) is not int or self.capacite <= 0:
            raise DonneeInvalide(
                "capacite", self.capacite, "entier strictement positif"
            )
        if self.code in self.prerequis:
            raise DonneeInvalide(
                "prerequis", self.code, "une UE n'est pas son propre prérequis"
            )

    def est_ouverte_a(self, etudiant: Etudiant) -> bool:
        """Vrai si l'UE est de son niveau, en tronc commun ou de sa filière."""
        return self.niveau == etudiant.niveau and self.filiere in (
            "",
            etudiant.filiere,
        )

    def __eq__(self, autre: object) -> bool:
        if not isinstance(autre, UE):
            return NotImplemented
        return self.code == autre.code

    def __hash__(self) -> int:
        return hash(self.code)

    def __str__(self) -> str:
        return f"{self.code} {self.intitule} ({self.credits} cr.)"

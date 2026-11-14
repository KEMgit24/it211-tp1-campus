"""Personnes connues d'iPNet Campus : classe abstraite Personne, Etudiant, Enseignant."""

import re
from abc import ABC, abstractmethod
from datetime import date
from functools import total_ordering

from .erreurs import DonneeInvalide

MOTIF_COURRIEL = re.compile(r"[a-z0-9._-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.[a-z]{2,}")


@total_ordering
class Personne(ABC):
    """Ce qui est commun aux étudiants et aux enseignants. Ne s'instancie pas."""

    __slots__ = ("_nom", "_prenom", "_courriel")

    def __init__(self, nom: str, prenom: str, courriel: str) -> None:
        self.nom = nom  # chaque affectation passe par la propriété
        self.prenom = prenom
        self.courriel = courriel

    # nom, prénom, courriel : propriétés qui valident à chaque modification
    @property
    def nom(self) -> str:
        return self._nom

    @nom.setter
    def nom(self, valeur: str) -> None:
        propre = " ".join(str(valeur).split()).upper()
        if not propre:
            raise DonneeInvalide("nom", valeur, "obligatoire")
        self._nom = propre

    @property
    def prenom(self) -> str:
        return self._prenom

    @prenom.setter
    def prenom(self, valeur: str) -> None:
        propre = " ".join(str(valeur).split())
        if not propre:
            raise DonneeInvalide("prenom", valeur, "obligatoire")
        self._prenom = propre

    @property
    def courriel(self) -> str:
        return self._courriel

    @courriel.setter
    def courriel(self, valeur: str) -> None:
        propre = str(valeur).strip().lower()
        if not MOTIF_COURRIEL.fullmatch(propre):
            raise DonneeInvalide("courriel", valeur, "adresse mal formée")
        self._courriel = propre

    @property
    @abstractmethod
    def identifiant(self) -> str:
        """Identifiant unique et immuable (matricule, code d'enseignant)."""

    @abstractmethod
    def role(self) -> str:
        """Libellé du rôle, pour l'affichage."""

    def nom_complet(self) -> str:
        return f"{self.prenom} {self.nom}"

    def __str__(self) -> str:
        return f"{self.nom_complet()} ({self.role()} {self.identifiant})"

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.identifiant!r})"

    def __eq__(self, autre: object) -> bool:
        if not isinstance(autre, Personne):
            return NotImplemented
        return self.identifiant == autre.identifiant

    def __hash__(self) -> int:
        return hash(self.identifiant)

    def __lt__(self, autre: object) -> bool:
        if not isinstance(autre, Personne):
            return NotImplemented
        return (self.nom, self.prenom, self.identifiant) < (
            autre.nom,
            autre.prenom,
            autre.identifiant,
        )


class Etudiant(Personne):
    """Un étudiant (RG01 : matricule IPN-AAAA-NNNN, unique et immuable)."""

    __slots__ = ("_matricule", "_filiere", "_niveau", "_date_naissance", "archive")

    MOTIF_MATRICULE = re.compile(r"IPN-\d{4}-\d{4}")
    FILIERES = ("ISI", "CYB", "DSB")
    NIVEAUX = ("L1", "L2", "L3")

    def __init__(
        self,
        matricule: str,
        nom: str,
        prenom: str,
        courriel: str,
        filiere: str,
        niveau: str,
        date_naissance: date | str,
    ) -> None:
        propre = str(matricule).strip().upper()
        if not self.MOTIF_MATRICULE.fullmatch(propre):
            raise DonneeInvalide(
                "matricule", matricule, "format IPN-AAAA-NNNN attendu"
            )
        self._matricule = propre
        super().__init__(nom, prenom, courriel)
        self.filiere = filiere
        self.niveau = niveau
        self.date_naissance = date_naissance
        self.archive = False

    @property
    def matricule(self) -> str:
        return self._matricule

    @property
    def identifiant(self) -> str:
        return self._matricule

    def role(self) -> str:
        return "étudiant"

    @property
    def filiere(self) -> str:
        return self._filiere

    @filiere.setter
    def filiere(self, valeur: str) -> None:
        propre = str(valeur).strip().upper()
        if propre not in self.FILIERES:
            raise DonneeInvalide(
                "filiere", valeur, f"valeurs permises : {', '.join(self.FILIERES)}"
            )
        self._filiere = propre

    @property
    def niveau(self) -> str:
        return self._niveau

    @niveau.setter
    def niveau(self, valeur: str) -> None:
        propre = str(valeur).strip().upper()
        if propre not in self.NIVEAUX:
            raise DonneeInvalide(
                "niveau", valeur, f"valeurs permises : {', '.join(self.NIVEAUX)}"
            )
        self._niveau = propre

    @property
    def date_naissance(self) -> date:
        return self._date_naissance

    @date_naissance.setter
    def date_naissance(self, valeur: date | str) -> None:
        if isinstance(valeur, str):
            try:
                valeur = date.fromisoformat(valeur.strip())
            except ValueError:
                raise DonneeInvalide(
                    "date_naissance", valeur, "date AAAA-MM-JJ attendue"
                ) from None
        if (
            not isinstance(valeur, date)
            or not date(1900, 1, 1) <= valeur <= date.today()
        ):
            raise DonneeInvalide("date_naissance", valeur, "date passée attendue")
        self._date_naissance = valeur

    def age(self, reference: date) -> int:
        """Âge révolu à la date de référence."""
        n = self._date_naissance
        return (
            reference.year
            - n.year
            - ((reference.month, reference.day) < (n.month, n.day))
        )


class Enseignant(Personne):
    """Un enseignant, identifié par un code ENS-NNN."""

    __slots__ = ("_code", "grade")

    MOTIF_CODE = re.compile(r"ENS-\d{3}")
    GRADES = (
        "Professeur",
        "Maître de conférences",
        "Maître-assistant",
        "Assistant",
        "Vacataire",
    )

    def __init__(
        self, code: str, nom: str, prenom: str, courriel: str, grade: str
    ) -> None:
        propre = str(code).strip().upper()
        if not self.MOTIF_CODE.fullmatch(propre):
            raise DonneeInvalide("code", code, "format ENS-NNN attendu")
        self._code = propre
        super().__init__(nom, prenom, courriel)
        if grade not in self.GRADES:
            raise DonneeInvalide("grade", grade, "grade inconnu")
        self.grade = grade

    @property
    def code(self) -> str:
        return self._code

    @property
    def identifiant(self) -> str:
        return self._code

    def role(self) -> str:
        return "enseignant"

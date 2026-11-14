"""Inscription d'un étudiant à une UE pour une année : porte les notes (RG03 à RG06, RG11)."""

import re
from decimal import Decimal

from . import regles
from .erreurs import DonneeInvalide, NotesVerrouillees
from .personnes import Etudiant
from .ue import UE

MOTIF_ANNEE = re.compile(r"(\d{4})-(\d{4})")


class Inscription:
    """Lien entre un étudiant et une UE pour une année universitaire."""

    __slots__ = (
        "_etudiant",
        "_ue",
        "_annee",
        "_note_cc",
        "_note_examen",
        "_publiee",
    )

    def __init__(self, etudiant: Etudiant, ue: UE, annee: str) -> None:
        m = MOTIF_ANNEE.fullmatch(annee)
        if not m or int(m[2]) != int(m[1]) + 1:
            raise DonneeInvalide(
                "annee", annee, "forme AAAA-AAAA, années consécutives"
            )
        self._etudiant = etudiant
        self._ue = ue
        self._annee = annee
        self._note_cc: Decimal | None = None
        self._note_examen: Decimal | str | None = None
        self._publiee = False

    # étudiant, UE et année forment la clé : lecture seule
    @property
    def etudiant(self) -> Etudiant:
        return self._etudiant

    @property
    def ue(self) -> UE:
        return self._ue

    @property
    def annee(self) -> str:
        return self._annee

    @property
    def publiee(self) -> bool:
        return self._publiee

    def publier(self) -> None:
        """Verrouille les notes (RG11) ; le registre l'appelle pour toute une UE."""
        self._publiee = True

    def _ecrire_corrigee(self, champ: str, valeur: object) -> None:
        """Réservée à Scolarite.corriger : modifie une note publiée, sous contrôle."""
        absence = champ == "note_examen"
        nouvelle = self._convertir(valeur, absence_permise=absence)
        if champ == "note_cc":
            self._note_cc = nouvelle
        else:
            self._note_examen = nouvelle

    @property
    def cle(self) -> tuple[str, str, str]:
        """Identifiant de l'inscription (matricule, code de l'UE, année)."""
        return (self.etudiant.matricule, self.ue.code, self.annee)

    @staticmethod
    def _convertir(valeur: object, absence_permise: bool) -> Decimal | str | None:
        """Accepte None, Decimal, int ou texte ; refuse les flottants (RG03)."""
        if valeur is None:
            return None
        if isinstance(valeur, float):
            raise TypeError(
                "note flottante refusée : passer une chaîne ou un Decimal"
            )
        try:
            return regles.lire_note(str(valeur), absence_permise=absence_permise)
        except ValueError as e:
            raise DonneeInvalide("note", valeur, str(e)) from None

    def _verifier_ouverte(self) -> None:
        if self._publiee:
            raise NotesVerrouillees(
                f"notes publiées ({self.ue.code}) : utiliser corriger()"
            )

    @property
    def note_cc(self) -> Decimal | None:
        return self._note_cc

    @note_cc.setter
    def note_cc(self, valeur: object) -> None:
        self._verifier_ouverte()
        self._note_cc = self._convertir(valeur, absence_permise=False)

    @property
    def note_examen(self) -> Decimal | str | None:
        return self._note_examen

    @note_examen.setter
    def note_examen(self, valeur: object) -> None:
        self._verifier_ouverte()
        self._note_examen = self._convertir(valeur, absence_permise=True)

    @property
    def note_finale(self) -> Decimal | None:
        """Recalculée à chaque lecture : jamais en désaccord avec les notes."""
        return regles.note_finale(self._note_cc, self._note_examen)

    @property
    def decision(self) -> str:
        return regles.decision(self.note_finale, self._note_examen)

    @property
    def complete(self) -> bool:
        """Vrai si les deux notes sont saisies (ABS compte comme saisie)."""
        return self._note_cc is not None and self._note_examen is not None

    def __repr__(self) -> str:
        return (
            f"Inscription({self.etudiant.matricule!r}, {self.ue.code!r}, "
            f"{self.annee!r}, "
            f"cc={self._note_cc}, examen={self._note_examen})"
        )

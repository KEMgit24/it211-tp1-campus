"""Paquet campus : modèle objet du domaine d'iPNet Campus (IT 211, séance 2)."""

from .erreurs import (
    DonneeInvalide,
    DoublonInterdit,
    ErreurCampus,
    InscriptionRefusee,
    NotesVerrouillees,
)
from .inscription import Inscription
from .personnes import Enseignant, Etudiant, Personne
from .scolarite import Scolarite
from .ue import UE

__all__ = [
    "DonneeInvalide",
    "DoublonInterdit",
    "ErreurCampus",
    "InscriptionRefusee",
    "NotesVerrouillees",
    "Enseignant",
    "Etudiant",
    "Inscription",
    "Personne",
    "Scolarite",
    "UE",
]

"""Exceptions métier d'iPNet Campus.

Toutes dérivent d'ErreurCampus : un appelant peut rattraper « toute erreur métier »
sans rattraper pour autant une faute de programmation.
"""


class ErreurCampus(Exception):
    """Racine des erreurs métier."""


class DonneeInvalide(ErreurCampus, ValueError):
    """Une valeur ne respecte pas une règle de gestion (RG01 à RG03, RG13)."""

    def __init__(self, champ: str, valeur: object, motif: str) -> None:
        super().__init__(f"{champ} = {valeur!r} : {motif}")
        self.champ = champ
        self.valeur = valeur
        self.motif = motif


class DoublonInterdit(ErreurCampus):
    """Un identifiant ou une adresse existe déjà (RG01, RG02, RG13)."""


class InscriptionRefusee(ErreurCampus):
    """Inscription contraire à RG09 ou RG10 ; motifs donne toutes les raisons."""

    def __init__(self, matricule: str, code_ue: str, motifs: list[str]) -> None:
        super().__init__(
            f"inscription de {matricule} à {code_ue} refusée : "
            + " ; ".join(motifs)
        )
        self.matricule = matricule
        self.code_ue = code_ue
        self.motifs = list(motifs)


class NotesVerrouillees(ErreurCampus):
    """Notes publiées : seule une correction motivée est possible (RG11)."""

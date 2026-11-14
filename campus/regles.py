"""Règles de gestion d'iPNet Campus (cahier des charges, RG03 à RG08).

Fonctions pures : aucune lecture de fichier, aucun affichage. Les notes sont des Decimal.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

POIDS_CC = Decimal("0.4")
POIDS_EXAMEN = Decimal("0.6")
CENTIEME = Decimal("0.01")
QUART = Decimal("0.25")
SEUIL = Decimal("10")
ABS = "ABS"


def lire_note(texte: str, *, absence_permise: bool = False) -> Decimal | str | None:
    """Convertit le texte d'une case de tableur en note (RG03).

    Renvoie None si la case est vide, ABS pour une absence (si elle est permise),
    un Decimal sinon. Lève ValueError, avec un message en français, si le texte
    est invalide.
    """
    t = texte.strip()
    if t == "":
        return None
    if t.upper() == ABS:
        if absence_permise:
            return ABS
        raise ValueError("« ABS » n'est admis que pour la note d'examen")
    try:
        note = Decimal(t.replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"« {t} » n'est pas un nombre") from None
    if not note.is_finite():
        raise ValueError(f"« {t} » n'est pas un nombre")
    if not Decimal(0) <= note <= Decimal(20):
        raise ValueError(f"{t} est hors de l'intervalle [0 ; 20]")
    if note % QUART != 0:
        raise ValueError(f"{t} n'est pas un multiple de 0,25")
    return note


def arrondir(x: Decimal) -> Decimal:
    """Arrondi au centième, demie vers le haut (RG04)."""
    return x.quantize(CENTIEME, rounding=ROUND_HALF_UP)


def note_finale(cc: Decimal | None, examen: Decimal | str | None) -> Decimal | None:
    """Note finale d'une UE (RG04, RG05) ; None si elle est incalculable."""
    if cc is None or examen is None or examen == ABS:
        return None
    return arrondir(POIDS_CC * cc + POIDS_EXAMEN * examen)


def decision(finale: Decimal | None, examen: Decimal | str | None) -> str:
    """Décision pour une UE (RG05, RG06)."""
    if examen == ABS:
        return "ABS"
    if finale is None:
        return "incomplet"
    return "validée" if finale >= SEUIL else "non validée"


def moyenne_ponderee(resultats: list[tuple[Decimal | None, int]]) -> Decimal:
    """Moyenne des notes finales pondérée par les crédits (RG07).

    resultats : couples (note finale ou None, crédits) ; None compte pour 0.
    """
    total_credits = sum(credits for _, credits in resultats)
    if total_credits == 0:
        raise ValueError("aucune UE : moyenne impossible")
    total = sum(
        (n if n is not None else Decimal(0)) * credits for n, credits in resultats
    )
    return arrondir(total / total_credits)


def mention(moyenne: Decimal) -> str:
    """Mention selon la moyenne semestrielle (RG08)."""
    if moyenne >= 16:
        return "Très bien"
    if moyenne >= 14:
        return "Bien"
    if moyenne >= 12:
        return "Assez bien"
    if moyenne >= 10:
        return "Passable"
    return "Non admis"

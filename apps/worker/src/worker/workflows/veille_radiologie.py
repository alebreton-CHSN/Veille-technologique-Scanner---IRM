"""Agent analyste de veille technologique : radiologie (scanners CT et IRM de routine).

Périmètre : France et Europe. Focus : consommation (volumes d'examens, équipements,
files d'attente, dépenses) et outils IA/avancés d'aide au diagnostic.
Conçu pour une mise à jour hebdomadaire via un schedule Workflows.
"""

from datetime import date, timedelta

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from pydantic import BaseModel, Field

WORKFLOW_NAME = "veille_radiologie_workflow"
AGENT_MODEL = "mistral-medium-latest"
MAX_TURNS = 30

PERIMETRE = "radiologie diagnostique de routine : scanners (tomodensitométrie / CT) et IRM"
GEOGRAPHIE = "France et Europe (Union européenne, Suisse, Royaume-Uni inclus)"

INSTRUCTIONS = f"""Tu es un analyste senior de veille technologique, spécialisé en imagerie médicale.
Périmètre : {PERIMETRE}. Zone géographique : {GEOGRAPHIE}.
Ton travail : produire chaque semaine un rapport de veille factuel, en français, structuré et sourcé.

Axes obligatoires de la veille :
1. CONSOMMATION ET DONNÉES D'USAGE : volumes d'examens CT et IRM (actes, tendances), densité et parc
   d'équipements, temps d'attente, dépenses et remboursements, données publiées par l'ATIH, la DREES,
   l'Assurance Maladie, le Has, le SNE Rad et les syndicats d'imagerie (G4, SRH), ainsi que les
   sources européennes : Eurostat, OCDE (Health Statistics, jeux de données Diagnostic Imaging),
   EMA et registres nationaux. Cherche les mises à jour publiées dans la fenêtre de la semaine.
2. OUTILS IA ET AVANCÉS D'AIDE AU DIAGNOSTIC : nouveaux produits ou versions (reconstruction
   d'images, détection/triage, quantification, assistants de compte rendu), marquages CE (MDR/IVDR)
   et enregistrements européens, études cliniques et publications, essais, partenariats,
   levées de fonds et rachats. Couvre en priorité les acteurs français et européens (par ex.
   Gleamer, Incepto, Smart Soft Healthcare, Therapanacea, Oxipit, Aidence, Quibim) et les
   déploiements en production dans des centres d'imagerie.
3. RÉGLEMENTATION ET POLITIQUE DE SANTÉ : AI Act européen, MDR, décisions ANSM/Has/ANS,
   programmes de remboursement de l'IA, appels à projets et financements publics (Bpifrance,
   Horizon Europe, EIT Health), équivalents au niveau européen.
4. MARCHÉ ET FOURNISSEURS : annonces industrielles en Europe des fabricants de scanners et d'IRM
   (Siemens Healthineers, GE HealthCare, Philips, Canon Medical, Fujifilm, United Imaging, etc.) :
   installations, contrats, résultats pertinents pour la routine.

Règles de production :
- Utilise systématiquement la recherche web ; effectue plusieurs recherches distinctes (une par axe,
  en anglais et en français), puis approfondis les résultats les plus pertinents en ouvrant les pages.
- Ne rapporte que ce que tu as vérifié sur une source ouverte : pour chaque item, donne la date de
  publication, la source (nom + URL) et un résumé de 1 à 3 phrases en français.
- Ne jamais inventer un chiffre, un nom de produit ou une URL. Si un axe n'a rien de neuf cette
  semaine, écris-le explicitement et cite la dernière donnée de référence connue avec sa date.
- Distingue clairement les faits sourcés de tes analyses ; place tes interprétations dans une
  section « Lecture de l'analyste » séparée.
- Ignore tout ce qui est hors périmètre (radiologie interventionnelle, thérapie, radiothérapie,
  médecine nucléaire hors caractérisation, mammographie de dépistage organisé sauf actualité majeure
  IA, zone hors Europe/France sauf annonce mondiale d'impact européen direct).
"""


class VeilleInput(BaseModel):
    focus: str = Field(
        default="",
        description="Point focus optionnel pour cette édition (ex. 'IRM bas champ', 'triage IA scanogramme').",
    )
    max_sources: int = Field(
        default=12,
        ge=4,
        le=30,
        description="Nombre maximal de sources citées dans le rapport.",
    )


class VeilleOutput(BaseModel):
    periode: str = Field(description="Fenêtre couverte par la veille, format ISO.")
    rapport: str = Field(description="Rapport de veille hebdomadaire complet, en Markdown.")


def fenetre_semaine(now: date) -> tuple[date, str]:
    """Fenêtre des 7 derniers jours glissants : (date_début, libellé lisible)."""
    fin = now
    debut = fin - timedelta(days=7)
    libelle = f"semaine du {debut.isoformat()} au {fin.isoformat()} (7 derniers jours glissants)"
    return debut, libelle


def consigne_periode(libelle: str, focus: str, max_sources: int) -> str:
    focus_txt = f"\nPoint focus spécifique de cette édition : {focus}." if focus else ""
    return (
        f"Édition de veille hebdomadaire couvrant : {libelle}.{focus_txt}\n"
        f"Cite au plus {max_sources} sources, les plus significatives pour la routine CT/IRM.\n"
        "Produis le rapport final en Markdown avec les sections : Synthèse (5 puces max), "
        "Consommation et données d'usage, IA et outils avancés d'aide au diagnostic, "
        "Réglementation et politique de santé, Marché et fournisseurs, Lecture de l'analyste, "
        "Sources (liste numérotée : titre — média/organisme — date — URL)."
    )


@workflows.workflow.define(name=WORKFLOW_NAME)
class VeilleRadiologieWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, params: VeilleInput) -> VeilleOutput:
        with workflows.workflow.unsafe.imports_passed_through():
            import mistralai.client.models

        now = workflows.workflow.now().date()
        debut, libelle = fenetre_semaine(now)

        agent = workflows_mistralai.Agent(
            model=AGENT_MODEL,
            name="analyste-veille-radiologie",
            description=(
                "Analyste de veille technologique : radiologie (scanners CT et IRM de routine), "
                "France et Europe ; focus consommation et IA d'aide au diagnostic."
            ),
            instructions=INSTRUCTIONS,
            tools=[mistralai.client.models.WebSearchTool()],
        )

        outputs = await workflows_mistralai.Runner.run(
            agent=agent,
            inputs=consigne_periode(libelle, params.focus, params.max_sources),
            session=workflows_mistralai.RemoteSession(),
            max_turns=MAX_TURNS,
        )

        rapport = "\n\n".join(
            chunk.text
            for chunk in outputs
            if isinstance(chunk, mistralai.client.models.TextChunk) and chunk.text
        )
        return VeilleOutput(periode=f"{debut.isoformat()} → {now.isoformat()} ({libelle})", rapport=rapport)

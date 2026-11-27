# veille-radiologie

Agent analyste de veille technologique exécuté comme workflow Mistral durable.

**Sujet** : radiologie diagnostique de routine — scanners (CT) et IRM.
**Zone** : France et Europe.
**Focus** : consommation (volumes d'examens, parc d'équipements, temps d'attente, dépenses) et outils IA/avancés d'aide au diagnostic (marquage CE/MDR, produits, publications, financements, déploiements).
**Cadence** : hebdomadaire, via un schedule Workflows (Europe/Paris).

## Contenu

- `apps/worker/src/worker/workflows/veille_radiologie.py` — workflow `veille_radiologie_workflow` : un agent durable (`mistral-medium-latest`) avec recherche web (`WebSearchTool`) qui produit un rapport hebdomadaire structuré et sourcé en Markdown.
- `apps/worker/tests/` — tests de découverte et unitaires (fenêtre de 7 jours, consigne, validation des entrées).

## Utilisation

Exécution manuelle : `execute_workflow` sur le workflow `veille_radiologie_workflow` avec
`{"focus": "IRM bas champ", "max_sources": 12}` (les deux champs sont optionnels).

Mise à jour hebdomadaire : créer un schedule `mistral_mcp_create_workflow_schedule` (cron hebdo,
fuseau `Europe/Paris`) ciblant le deployment géré `veille-radiologie-worker`.

## Développement

```bash
bunx nx run worker:semgrep   # règles workflow (obligatoire, 0 blocking)
cd apps/worker && uv run --all-packages --with pytest pytest tests/ -q
```

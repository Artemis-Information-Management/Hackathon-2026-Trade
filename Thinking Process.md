# Thinking process

*Trade Hackathon 2026 · Luxembourg — team Dat'Artemis. Version française plus bas.*

**Starting point.** The challenge asks what Luxembourg trades, with whom, how it changes and how Luxembourg compares with other countries. Our goal: one tool that answers those questions for someone who is not a trade statistician.

**1. Which data?** Eurostat Comext (ds-045409). We started from Excel downloads; The first challenge was to decide how to deal with that amount of data. We decided to run processes separately, an extraction using R, another one with Python.  At the beginning though, we chose to download the first part of the data manually, so that we could start working on it directly. However, since we wanted to improve the downloading process, we worked in parallel to extract the data using API instead of doing manually. 

**2. How deep?** We mainly used 2 digits, and 4-digits for the drill-down graph from the summary . So: 97 HS2 chapters in every view, 4 digits only where it matters (the year's top 5).

**3. What form?** One self-contained HTML file, serverless: using R Markdown only to produce an offline functional dashboard.

**4. What to show first?** The Summary follows the challenge questions in order: the year in figures, the top 5 products (click to zoom), the four neighbours, the trade balance, then product dependence. The other views go deeper: Overview (partners on a map), Product (how many partners a product relies on), Country (one partner or region), Trade twins.

**5. How to say a product is a dependence?** Three simple criteria, flagged or not: weight ≥ 2 % of trade, partner concentration HHI ≥ 0.25, net import dependence ≥ 50 %. Three flags = critical, none = low. Simple enough to be read without a legend.

**6. How to compare countries?** The Trade twins: which EU countries buy or sell the same *mix* of products as Luxembourg (Finger-Kreinin index, 0 to 100). First built apart, on exports only; then a tab of the page, on both flows, with the score taken apart product by product and a product picker.

**Next.** Compare a twin's clients with ours to list the markets where a supplier like us already sells and Luxembourg is absent.

---

# Cheminement de pensée (FR)

*Trade Hackathon 2026 · Luxembourg — équipe Dat'Artemis.*

**Point de départ.** Le défi demande ce que le Luxembourg échange, avec qui, comment cela évolue et comment le Luxembourg se compare aux autres pays. Notre objectif : un outil qui répond à ces questions pour quelqu'un qui n'est pas statisticien du commerce.

**1. Quelles données ?** Eurostat Comext (ds-045409). Nous sommes partis de téléchargements Excel ; le premier défi a été de décider comment traiter ce volume de données. Nous avons choisi de séparer les traitements : une extraction avec R, une autre avec Python. Au départ, nous avons choisi de télécharger manuellement la première partie des données, pour pouvoir commencer à travailler dessus tout de suite. Mais comme nous voulions améliorer le processus de téléchargement, nous avons travaillé en parallèle sur une extraction des données par l’API, à la place du téléchargement manuel.

**2. Quelle profondeur ?** Nous avons surtout utilisé le niveau 2 chiffres, et le niveau 4 chiffres pour le graphique de zoom du Summary. Donc : les 97 chapitres HS2 dans toutes les vues, le niveau 4 chiffres seulement là où ça compte (le top 5 de l'année).

**3. Quelle forme ?** Un seul fichier HTML autonome, sans serveur : uniquement R Markdown, pour produire un tableau de bord fonctionnel hors ligne.

**4. Quoi montrer en premier ?** Le Summary suit les questions du défi dans l'ordre : l'année en chiffres, le top 5 des produits (cliquer pour zoomer), les quatre voisins, la balance commerciale, puis la dépendance par produit. Les autres vues creusent : Overview (les partenaires sur une carte), Product (de combien de partenaires dépend un produit), Country (un partenaire ou une région), Trade twins.

**5. Comment dire qu'un produit est une dépendance ?** Trois critères simples, atteints ou non : poids ≥ 2 % du commerce, concentration des partenaires HHI ≥ 0,25, dépendance nette aux imports ≥ 50 %. Trois drapeaux = critique, aucun = faible. Assez simple pour se lire sans légende.

**6. Comment comparer les pays ?** Les Trade twins : quels pays de l'UE achètent ou vendent le même *panier* de produits que le Luxembourg (indice de Finger-Kreinin, de 0 à 100). D'abord construits à part, sur les exportations seulement ; puis un onglet de la page, sur les deux flux, avec le score décomposé produit par produit et un sélecteur de produit.

**La suite.** Comparer les clients d'un jumeau aux nôtres pour lister les marchés où un fournisseur comme nous vend déjà et où le Luxembourg est absent.

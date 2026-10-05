# Guide Node Registry — v488.18 Draft

## Status

**DRAFTED — not installed, not activated, not live E2E verified.**

Base production remains v488.17.

Draft branch:

`guide-node-registry-v488.18-draft`

## Purpose

Extend The Guide so that a visitor can arrive at a meaningful destination in the Living Archive without first understanding the Archive's menu architecture.

The menu remains the map.

The Guide becomes the wayfinding layer across that map.

A Guide Node is a destination worth arriving at: a substantive experience, reference system, pathway, navigator, framework, hub, or collection that can answer a recognizable visitor need.

## Architectural boundary

```
WordPress navigation
        |
        v
Guide Node Registry
        |
        v
The Guide / USE
        |
        +--> native specialist/tool
        |
        +--> native Guide Node
        |
        +--> ordinary Guide response
```

WordPress is authoritative for structure and canonical URLs.

The registry is authoritative only for **approved Guide Nodes**, not for the entire site.

USE is responsible for interpreting the visitor's question and selecting the appropriate route.

Native tools remain responsible for their own experience.

## What this is not

- Not a site-wide crawler.
- Not conventional search.
- Not a second content corpus.
- Not a Pinecone index.
- Not a duplicate implementation of specialist tools.
- Not automatic promotion of every menu item into a Guide Node.
- Not title matching.

## Node qualification

A destination is eligible when it is substantive, recognizable, stable, publicly appropriate, and useful enough that surfacing it reduces visitor friction.

Depth is a discovery signal, not a qualification criterion.

Containers such as "Resources", "Core Pathways", "Stewardship Practice", and "Knowledge Hubs" remain architectural containers unless they themselves provide a substantive experience.

## First approved draft nodes

The first registry deliberately favors destinations whose public pages demonstrate an actual experience or structured body of work:

| Node | Type | Access |
|---|---|---|
| Fractal Systems Diagnostic | diagnostic | public |
| Living Glossary | reference system | public |
| Guardian Glyph Archives | searchable archive | public |
| Philippine Systems, Society, and Culture | knowledge hub | public |
| Philippine Renewal Framework | knowledge hub | public |
| Access the Institute Case Library | access gateway | mixed |
| Learning Arcs | learning pathway | steward |
| Stewardship Case Atlas | case library | purchase |
| Applied Stewardship Toolkit | toolkit | public |

The public Archive confirms that these destinations have substantive functions. For example, the FSD describes itself as an orientation device that identifies places to look within the Archive; the Glossary defines recurring Archive vocabulary; the Case Library gateway explicitly directs visitors according to learning goals; and the Learning Arcs form a sequenced educational architecture. 

## Access boundaries

The registry carries access class so The Guide can distinguish:

- `public`
- `mixed`
- `steward`
- `protected`
- `purchase`

A restricted node may be discoverable when the visitor's intent clearly calls for it, but the Guide must never imply that access is included when it is not.

## WordPress plugin

The draft plugin is intentionally small.

It exposes:

- `GET /wp-json/guide/v1/nodes`
- `GET /wp-json/guide/v1/navigation`

The first returns approved Guide Nodes.

The second exposes the actual WordPress navigation structures available to the site, supporting both classic menus and the `wp_navigation` block-navigation post type.

This gives us two separate truths:

1. **Structural truth:** what WordPress currently serves as navigation.
2. **Curated truth:** which destinations are meaningful enough to be Guide Nodes.

The two should not be conflated.

## USE handoff contract

When USE has already determined that a visitor should go to a specific Guide Node, the native handoff envelope is:

```json
{
  "intent": "GUIDE_NODE_HANDOFF",
  "handoff": "guide_node",
  "handoff_mode": "direct",
  "handoff_pending": true,
  "guide_node_id": "…",
  "guide_node_title": "…",
  "guide_node_url": "https://geralddaquila.com/…",
  "guide_node_access_class": "public",
  "return_mode": "native_guide_node"
}
```

The node layer does not determine intent. It packages the already-made routing decision safely.

## Pinecone

Pinecone is not required for this layer.

The registry answers:

> Where are the meaningful places?

Semantic retrieval answers:

> What evidence is relevant?

Those are different problems.

Pinecone can be considered later if node ambiguity becomes sufficiently large to justify semantic disambiguation. It must not become the authority for Archive architecture.

## Reconciliation with WPVibe

When WPVibe becomes available:

1. Activate the draft plugin in a controlled manner.
2. Read `/wp-json/guide/v1/navigation`.
3. Compare its live structural output with the public navigation map.
4. Read `/wp-json/guide/v1/nodes`.
5. Reconcile URLs, labels, hierarchy, and access classes.
6. Add or remove nodes only where the live structure and visitor value justify it.
7. Only then integrate the registry into the production Guide route.
8. Perform live visitor E2E tests.

The status progression is:

`DRAFTED → RECONCILED → INSTALLED → LIVE E2E VERIFIED`

No later state should be claimed before it actually occurs.

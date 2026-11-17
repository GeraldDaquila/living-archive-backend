# SPE frontend source snapshot

This directory mirrors the visitor-facing HTML, CSS, and JavaScript assets deployed in the active WordPress Stewardship Pathway Engine plugin. The production plugin's PHP engine and canonical data remain in its installed plugin directory. UI asset changes must be synchronized to `wp-content/plugins/stewardship-pathway-engine-v3.4.2-formation-boundary-resilience/assets/` and its bootstrap must enqueue `la-answer-doorway-standard` as a script dependency.

The SPE three-door selection and ordering remain owned by SPE. The shared doorway renderer owns presentation and canonical URL validation only.

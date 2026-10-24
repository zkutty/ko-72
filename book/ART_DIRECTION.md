# Kō illustration direction — pilot v1

Status: proposed visual system. Compare four pilot images together before approving this for all 72 seasons.

## Core image grammar

- **Medium:** quiet editorial nature plate, as if fine sumi ink line and diluted mineral pigment were applied to warm, lightly textured washi. Visible hand-made edges, restrained pigment pooling, and modest paper grain. Avoid photographic detail and polished digital gradients.
- **Composition:** portrait page, one legible seasonal event or subject at human scale. Place the focal action in the middle 70% of the page; leave generous paper around it. A small suggestion of habitat may anchor the subject, but do not make a scenic panorama or decorative border.
- **Line:** fine, slightly broken dark-brown ink. Vary line weight with restraint. The drawing should read at book size and in a thumbnail contact sheet.
- **Color:** Kō washi `#f5f3ee` and ink `#1a1a18` are constants. One major-season pigment dominates: spring bamboo `#6b8f71`, summer persimmon `#c9734a`, autumn harvest gold `#d4a853`, winter sky `#4a7fa5`. Supporting browns/greys are muted; local subject colors may appear in low saturation. Avoid bright neon, heavy black fills, or a four-color rainbow palette.
- **Typography:** none inside the illustration. Japanese characters, English title, season number, and folio are typeset separately so they remain accurate and editable.
- **Mood:** attentive, specific, still. The art is a field observation, not a fantasy landscape, lifestyle scene, or souvenir print.

## Consistency and accuracy review

Every image should depict the named micro-season clearly without inventing a festival, building, person, species, or food claim. Review actual subject anatomy and habitat before final approval. Reject accidental lettering, watermarks, border ornaments, generic cherry-blossom symbolism, and recurring compositions that make distinct seasons indistinguishable.

Pilot subjects:

| ID | Major season | Subject | Source boundary |
|---:|---|---|---|
| 24 | Spring | A single peony opening, with two buds and sparse leaves | Bilingual cached letter exists; image remains a visual interpretation |
| 38 | Summer | A lotus opening above a quiet pond, with one leaf and reflection | Bilingual cached letter exists; image remains a visual interpretation |
| 55 | Autumn | Wild geese crossing high above a reed-fringed wetland | Bilingual cached letter exists; image remains a visual interpretation |
| 1 | Winter | Water parsley emerging beside a cold shallow stream | Calendar metadata only; no cached winter letter yet |

## Production rules

Save the original built-in imagegen output and full prompt for each pilot. Record tool/model disclosure, generated date, pixel dimensions, intended page crop, and review status in `art_manifest.json`. Never identify a generated image as print-ready solely by its pixel dimensions. The final printer choice controls color handling, bleed, effective PPI, and export settings. A human-scale contact sheet is the first style acceptance gate.

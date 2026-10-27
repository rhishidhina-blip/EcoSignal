**Completed in the numerical GeoRisk combined release.** Original pending checkpoint notes follow for provenance.

# Pending combined update — after Site v21

Current published version remains v21 (source 68de6796dbf5f289bfdc81b4db82cdf58d0cc57c). No separate deployment is requested for this checkpoint. Combine this responsive fix with the incoming numerical GeoRisk integration before publication. Existing v20/v21 source and published versions remain preserved.

## LichenLens narrow-layout fix

User observed horizontal overflow in the authenticated Site preview around 320 px, including the Photograph/Context/Results strip and scan content. The responsive scan grid now has an explicit zero minimum; children and form controls can shrink, long labels wrap, and at 320–390 px each of the three steps puts its numbered badge above its label. At narrow widths context fields, result cards, photo/mask panels and result actions stack. Screening explanations and buttons are also constrained to their available width. Desktop column sizes and step arrangement remain unchanged.

Checks: Site build and existing software regressions run for this checkpoint. Browser viewport/scroll-width verification is pending: the user has authenticated preview access, but this environment does not have the supported browser-QA capability. No claim of visual verification at 320/360/375/390 px is made. User-observed QA should check Photograph, Context and Results (including the illustrated and imported-result states) at those widths before combined publication.

## User-reported numerical recovery progress

As of Oct 12, 2026, 21:46 America/New_York: inference approximately 1775/2393 original tiles, same frozen model and original 1 m features, full reverified DEM hashes. Portable model parity independently checked, max difference 1.574e-7. Expected product is a documented **20 m sample lattice**, not PNG-derived values or a native 1 m susceptibility raster. Preserve native-feature resolution, sample spacing, footprint and geographic transform as separate provenance.

These are user-reported progress facts; export bytes/hashes have not yet been received or independently verified here. No partial inference output is integrated into scoring. The complete revised notebook reportedly ran with the real satellite ZIP and zero real sites, passed nine assertions and exported unavailable diagnostics without crashing. This confirms reported execution robustness, not scientific validation or observed complete-score availability. Full-score eligibility remains unchanged until numerical grid/reference and eligible real observation inputs exist.

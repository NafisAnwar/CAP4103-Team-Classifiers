# Dataset protocol: pending N2/N3

The October course PDF lists Olivetti and BMPD as approved. Actual acquisition, source terms, permitted use and image-quality audit are pending. `data/raw/face/` and `data/raw/palm/` are local ignored storage locations.

The proposed design uses original usable unblurred Olivetti images and BMPD right palms, with explicitly artificial user pairing. Inspect actual palm filename labels, sessions, sample counts, duplicate captures and ROI quality before finalizing selection. Do not silently substitute another dataset. Do not assume all captures have good lighting.

Record provenance, download date, terms, actual per-identity counts, hand/session tags, decoding failures and exclusion reasons. Review ROI contact sheets locally before claiming reliable palm features. Keep source images out of Git and shared report materials unless usage terms permit them.

The draft seed/split/count values live in `configs/protocol.proposed.json`. They are hypotheses, not observed counts. Create actual manifests only after the audit; use the field contracts in `data_contracts.md`.

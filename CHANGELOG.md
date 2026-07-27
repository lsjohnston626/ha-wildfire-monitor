# Changelog

All notable changes to Wildfire Monitor are documented here. This project uses
[Semantic Versioning](https://semver.org/).

## 0.2.3 - 2026-07-27

- Reject malformed or truncated upstream feature responses instead of treating
  them as an authoritative empty result.
- Prevent a fire that briefly disappears from producing a duplicate
  `fire_entered_perimeter` event when it returns.
- Add first-party test and Ruff checks to the repository validation workflow.
- Improve internal typing, deduplication, and event documentation.

## 0.2.2 - 2026-07-27

- Add individually named, translated automation triggers to Home Assistant's
  trigger catalog.

## 0.2.1 - 2026-07-27

- Add device automation triggers for all wildfire transitions.

## 0.2.0 - 2026-07-27

- Add transition-safe wildfire, official alert, threat, evacuation, and source
  health events.

## 0.1.2 - 2026-07-26

- Update the HACS display name and repository branding.

## 0.1.1 - 2026-07-25

- Add translations for every Home Assistant locale.
- Link devices to the integration documentation.
- Correct HACS release downloads.

## 0.1.0 - 2026-07-25

- Initial release.

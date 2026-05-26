# aspect-data

Remote content data for the **Aspect** Marvel Champions companion app.

When FFG releases new content, edit the JSON files here and push.
The app fetches updates the next time the user taps **Kartendaten synchronisieren** in Settings.

## Files

### `data/scenarios.json`
Flat list of all playable scenarios, grouped by pack name.

```json
{ "pack": "Pack Name", "name": "Scenario Name", "sort": 31 }
```

To add a new pack: append its scenarios with sequential `sort` values (continue from the last number).

### `data/campaigns.json`
Campaign templates for the multi-player campaign tracker.

Each entry maps to an existing `CampaignType` in the app.
You can update `scenarios` (mission order) and `logItems` (campaign log checkboxes)
without an app update. Adding a *new* campaign type still requires an app release.

## After editing

Push to `main`. The raw file URL is immediately live:
```
https://raw.githubusercontent.com/YOUR_USERNAME/aspect-data/main/data/scenarios.json
https://raw.githubusercontent.com/YOUR_USERNAME/aspect-data/main/data/campaigns.json
```

These are the URLs to set in `src/features/cards/data/sync.ts`:
```typescript
const SCENARIOS_REMOTE_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/aspect-data/main/data/scenarios.json';
const CAMPAIGNS_REMOTE_URL = 'https://raw.githubusercontent.com/YOUR_USERNAME/aspect-data/main/data/campaigns.json';
```

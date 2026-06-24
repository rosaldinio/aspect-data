/**
 * Build-time script: fetches all Marvel Champions cards from marvelcdb.com
 * and writes a bundled JSON file into the Expo app assets.
 *
 * Run: node scripts/fetch-cards.mjs
 * Requires Node 18+ (native fetch).
 * Commit the resulting assets/data/cards.json — it is the app's data bundle.
 */

import { writeFileSync, mkdirSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = resolve(__dirname, '../temp_init/assets/data/cards.json');
const OUTPUT_DIR = resolve(__dirname, '../temp_init/assets/data');

const MARVELCDB_BASE = 'https://marvelcdb.com';
const CARDS_EN = `${MARVELCDB_BASE}/api/public/cards/`;
const CARDS_DE = `${MARVELCDB_BASE}/api/public/cards/?locale=de`;

async function fetchJson(url) {
  console.log(`  GET ${url}`);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status} – ${url}`);
  return res.json();
}

// Only store DE value if it actually differs from EN (marvelcdb often returns identical data)
function deOrNull(deVal, enVal) {
  if (!deVal || deVal === enVal) return null;
  return deVal;
}

function transformCard(en, de) {
  return {
    code: en.code,
    pack_code: en.pack_code ?? null,
    set_code: en.set_code ?? null,
    type_code: en.type_code ?? 'unknown',
    faction_code: en.faction_code ?? 'basic',
    position: en.position ?? 0,
    cost: en.cost ?? null,
    attack: en.attack ?? null,
    defense: en.defense ?? null,
    thwart: en.thwart ?? null,
    health: en.health ?? null,
    hand_size: en.hand_size ?? null,
    is_unique: en.is_unique ? 1 : 0,
    quantity: en.quantity ?? 1,
    duplicate_of_code: en.duplicate_of ?? null,
    imagesrc: en.imagesrc ?? null,
    name_en: en.name,
    subname_en: en.subname ?? null,
    text_en: en.text ?? null,
    traits_en: en.traits ?? null,
    flavor_en: en.flavor ?? null,
    name_de: deOrNull(de?.name, en.name),
    subname_de: deOrNull(de?.subname, en.subname),
    text_de: deOrNull(de?.text, en.text),
    traits_de: deOrNull(de?.traits, en.traits),
    flavor_de: deOrNull(de?.flavor, en.flavor),
  };
}

async function main() {
  console.log('Fetching Marvel Champions card data from marvelcdb.com…\n');

  const enCards = await fetchJson(CARDS_EN);
  console.log(`  ✓ ${enCards.length} EN cards\n`);

  let deMap = {};
  try {
    const deCards = await fetchJson(CARDS_DE);
    deMap = Object.fromEntries(deCards.map(c => [c.code, c]));
    console.log(`  ✓ ${deCards.length} DE cards\n`);
  } catch (e) {
    console.warn(`  ⚠ DE cards unavailable (${e.message}) — name_de/text_de will be null\n`);
  }

  const merged = enCards.map(card => transformCard(card, deMap[card.code]));

  mkdirSync(OUTPUT_DIR, { recursive: true });
  writeFileSync(OUTPUT_PATH, JSON.stringify(merged));

  console.log(`✓ Wrote ${merged.length} cards → ${OUTPUT_PATH}`);
  console.log('\nCommit assets/data/cards.json to include in the app bundle.');
}

main().catch(e => { console.error(e); process.exit(1); });

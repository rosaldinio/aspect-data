/**
 * Fetches villain HP and main scheme threat data from marvelcdb.com
 * and outputs ready-to-paste values for setup-guide-data.ts
 *
 * Run: node scripts/fetch-setup-data.mjs
 */

const CARDS_URL = 'https://marvelcdb.com/api/public/cards/?encounter=1';

// Maps scenario key → set_code(s) used to find villain + scheme cards
const SCENARIO_SETS = {
  'Rhino':                    { villain: ['rhino'], scheme: ['rhino'] },
  'Klaw':                     { villain: ['klaw'], scheme: ['klaw'] },
  'Ultron':                   { villain: ['ultron'], scheme: ['ultron'] },
  'Risky Business':           { villain: ['risky_business'], scheme: ['risky_business'] },
  'Mutagen Formula':          { villain: ['mutagen_formula'], scheme: ['mutagen_formula'] },
  'The Wrecking Crew':        { villain: ['wrecking_crew'], scheme: ['wrecking_crew'] },
  'Brotherhood of Badoon':    { villain: ['brotherhood_of_badoon'], scheme: ['brotherhood_of_badoon'] },
  'Infiltrate the Museum':    { villain: ['infiltrate_the_museum'], scheme: ['infiltrate_the_museum'] },
  'Escape the Museum':        { villain: ['escape_the_museum'], scheme: ['escape_the_museum'] },
  'Nebula':                   { villain: ['nebula_villain'], scheme: ['nebula_villain'] },
  'Ronan the Accuser':        { villain: ['ronan'], scheme: ['ronan'] },
  'Ebony Maw':                { villain: ['ebony_maw'], scheme: ['ebony_maw'] },
  'Tower Defense':            { villain: ['tower_defense'], scheme: ['tower_defense'] },
  'Thanos':                   { villain: ['thanos'], scheme: ['thanos'] },
  'Hela':                     { villain: ['hela'], scheme: ['hela'] },
  'Loki':                     { villain: ['loki_villain'], scheme: ['loki_villain'] },
  'Sandman':                  { villain: ['sandman'], scheme: ['sandman'] },
  'Venom':                    { villain: ['venom_villain'], scheme: ['venom_villain'] },
  'Mysterio':                 { villain: ['mysterio'], scheme: ['mysterio'] },
  'The Sinister Six':         { villain: ['sinister_six'], scheme: ['sinister_six'] },
  'Venom Goblin':             { villain: ['venom_goblin'], scheme: ['venom_goblin'] },
  'The Hood':                 { villain: ['hood'], scheme: ['hood'] },
  'Sabretooth':               { villain: ['sabretooth'], scheme: ['sabretooth'] },
  'Project Wideawake':        { villain: ['project_wideawake'], scheme: ['project_wideawake'] },
  'Master Mold':              { villain: ['master_mold'], scheme: ['master_mold'] },
  'Mansion Attack':           { villain: ['mansion_attack'], scheme: ['mansion_attack'] },
  'Magneto':                  { villain: ['magneto'], scheme: ['magneto'] },
  'Mojo Mania':               { villain: ['mojo_mania'], scheme: ['mojo_mania'] },
  'The Abandoned and Outcast':{ villain: ['abandoned_and_outcast'], scheme: ['abandoned_and_outcast'] },
  'Cascade of Consequences':  { villain: ['cascade'], scheme: ['cascade'] },
  'War for Salvation':        { villain: ['war_for_salvation'], scheme: ['war_for_salvation'] },
  'Apocalypse':               { villain: ['apocalypse'], scheme: ['apocalypse'] },
};

async function main() {
  console.log('Fetching all encounter cards from marvelcdb.com…');
  const res = await fetch(CARDS_URL);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const cards = await res.json();
  console.log(`  ✓ ${cards.length} cards loaded\n`);

  const villains = cards.filter(c => c.type_code === 'villain');
  const schemes  = cards.filter(c => c.type_code === 'main_scheme');
  console.log(`  Villain cards: ${villains.length}`);
  console.log(`  Main scheme cards: ${schemes.length}\n`);

  // Show all distinct set_codes for villains and schemes so we can fix mappings
  const villainSets = [...new Set(villains.map(c => c.card_set_code))].sort();
  const schemeSets  = [...new Set(schemes.map(c => c.card_set_code))].sort();
  console.log('=== Villain set_codes ===');
  console.log(villainSets.join('\n'));
  console.log('\n=== Main scheme set_codes ===');
  console.log(schemeSets.join('\n'));
  console.log('\n');

  // Output results for each scenario
  console.log('=== RESULTS ===\n');
  for (const [scenario, sets] of Object.entries(SCENARIO_SETS)) {
    const scenarioVillains = villains
      .filter(v => sets.villain.some(s => v.card_set_code?.includes(s)))
      .sort((a, b) => String(a.stage).localeCompare(String(b.stage)));

    const schemeStage1 = schemes
      .filter(s => sets.scheme.some(sc => s.card_set_code?.includes(sc)))
      .sort((a, b) => String(a.stage).localeCompare(String(b.stage)));

    const hasVillains = scenarioVillains.length > 0;
    const hasScheme = schemeStage1.length > 0;

    if (!hasVillains && !hasScheme) {
      console.log(`// ⚠ ${scenario}: no match found — check set_codes above`);
    } else {
      console.log(`// ${scenario}`);
    }

    if (hasScheme) {
      const s1 = schemeStage1[0];
      const threatInfo = s1.base_threat_fixed
        ? `${s1.base_threat} (fixed)`
        : `${s1.base_threat} (per player)`;
      const thresholdInfo = s1.threat_fixed
        ? `${s1.threat} (fixed)`
        : `${s1.threat} (per player)`;
      console.log(`  startingThreat: ${s1.base_threat},  // ${threatInfo}`);
      console.log(`  threatPerPlayer: ${s1.threat},       // threshold: ${thresholdInfo}`);
      if (s1.escalation_threat) console.log(`  accelerationTokens: ${s1.escalation_threat},`);
    }

    if (hasVillains) {
      console.log(`  villainStages: [`);
      scenarioVillains.forEach(v => {
        const hpNote = v.health_per_hero ? `${v.health} × players` : String(v.health);
        console.log(`    { name: '${v.name} ${v.stage}', hp: ${v.health} }, // ${hpNote}  health_per_hero: ${v.health_per_hero}  [set: ${v.card_set_code}]`);
      });
      console.log(`  ],`);
    }

    console.log('');
  }
}

main().catch(e => { console.error(e); process.exit(1); });

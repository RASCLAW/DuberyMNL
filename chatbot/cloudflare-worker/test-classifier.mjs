// Unit test for classifyIntent — copy of the function from worker.js
// Run: node test-classifier.mjs

function classifyIntent(text) {
  if (!text) return null;
  const lower = text.toLowerCase();

  // order_intent: phone (09xxxxxxxxx) + any address keyword
  const hasPhone = /\b09\d{9}\b/.test(text);
  const hasAddress = /\b(st\.?|street|brgy\.?|barangay|city|subd\.?|village|ave\.?|avenue|road|rd\.?|purok|sitio|phase|block|blk\.?|lot)\b/i.test(text);
  if (hasPhone && hasAddress) return "order_intent";

  // how_to_order (priority over pricing)
  if (/how to order|paano (po )?(mag[- ]?)?order|pano (po )?(mag[- ]?)?order|pa[- ]?order|order po\b|steps? to order/i.test(lower)) {
    return "how_to_order";
  }

  // pricing
  if (/\bhow much\b|\bmagkano\b|\bprice\b|\bpresyo\b|\bhm\b|\btag\??\b/i.test(lower)) {
    return "pricing";
  }
  if (/^how\s*\??$/i.test(lower.trim()) || /^\?+$/.test(lower.trim())) {
    return "pricing";
  }

  // shipping
  if (/\bship(ping|ment)?\b|\bsf\b|\bdelivery fee\b|\bmagkano ang ship\b|\bshipping fee\b/i.test(lower)) {
    return "shipping";
  }

  // polarized
  if (/polariz(ed|e)|\bpola\b/i.test(lower)) {
    return "polarized";
  }

  return null;
}

const cases = [
  // Mock test scenarios (from our walkthrough)
  { input: "How much po?",            expect: "pricing" },
  { input: "magkano?",                expect: "pricing" },
  { input: "hm",                      expect: "pricing" },
  { input: "Polarized ba yan?",       expect: "polarized" },
  { input: "sf po?",                  expect: "shipping" },
  { input: "paano mag order",         expect: "how_to_order" },
  { input: "Juan dela Cruz, 09171234567, 123 Mabini St Sampaloc Manila, Outback Blue, COD, 2pm", expect: "order_intent" },
  { input: "how much",                expect: "pricing" },
  { input: "polarized?",              expect: "polarized" },
  { input: "Hi",                      expect: null },

  // Kingpin edge cases
  { input: "how",                     expect: "pricing" },
  { input: "How",                     expect: "pricing" },
  { input: "how?",                    expect: "pricing" },
  { input: "?",                       expect: "pricing" },

  // Conversational follow-ups (should fall through to null → suppress-polite-hold)
  { input: "ok thanks",               expect: null },
  { input: "sige po",                 expect: null },
  { input: "meron Outback Blue?",     expect: null },
  { input: "legit ba?",               expect: null },

  // Pricing variations
  { input: "price po?",               expect: "pricing" },
  { input: "presyo?",                 expect: "pricing" },
  { input: "How much po 2 pairs?",    expect: "pricing" },

  // Shipping variations
  { input: "ship fee?",               expect: "shipping" },
  { input: "shipping fee po?",        expect: "shipping" },
  { input: "delivery fee?",           expect: "shipping" },

  // How-to-order variations
  { input: "how to order po",         expect: "how_to_order" },
  { input: "paano po mag order",      expect: "how_to_order" },
  { input: "pa-order po",             expect: "how_to_order" },

  // Order intent variations
  { input: "Juan, 09171234567, 45 Kalayaan Ave Diliman QC, Outback Blue, COD, noon",
    expect: "order_intent" },
  { input: "09171234567 Purok 2 Brgy San Roque Pasig City, Rasta Red, GCash",
    expect: "order_intent" },
  { input: "just my phone 09171234567, no address",
    expect: null }, // phone but no address keyword → falls through
  { input: "my address is UP Village QC",
    expect: null }, // address but no phone → falls through

  // Tricky cases
  { input: "order",                   expect: null }, // just "order" alone is ambiguous, no "po" or "how to"
  { input: "polarized daw",           expect: "polarized" },
  { input: "",                        expect: null },
];

let pass = 0, fail = 0;
const failures = [];

for (const { input, expect } of cases) {
  const actual = classifyIntent(input);
  if (actual === expect) {
    pass++;
  } else {
    fail++;
    failures.push({ input, expect, actual });
  }
}

console.log(`\n${pass}/${pass + fail} passed`);
if (failures.length) {
  console.log("\nFAILURES:");
  for (const f of failures) {
    console.log(`  input:    ${JSON.stringify(f.input)}`);
    console.log(`  expected: ${f.expect}`);
    console.log(`  actual:   ${f.actual}`);
    console.log();
  }
  process.exit(1);
}

#!/usr/bin/env node
// Unified DailyHotApi invocation script
// Usage: node fetch_dailyhot.mjs <source> [key=value ...]
// Examples:
//   node fetch_dailyhot.mjs hupu
//   node fetch_dailyhot.mjs hupu type=6
//   node fetch_dailyhot.mjs baidu type=realtime
//   node fetch_dailyhot.mjs github type=weekly
//   node fetch_dailyhot.mjs weibo

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error("Usage: node fetch_dailyhot.mjs <source> [key=value ...]");
  console.error("Example: node fetch_dailyhot.mjs hupu type=1");
  process.exit(1);
}

const source = args[0];
const params = {};
for (const arg of args.slice(1)) {
  const [k, v] = arg.split("=");
  if (k && v !== undefined) params[k] = v;
}

async function main() {
  const mod = await import(`dailyhot-api/dist/routes/${source}.js`);
  const handleRoute = mod.handleRoute || mod.default;
  if (typeof handleRoute !== "function") {
    console.error(`Error: dailyhot-api/dist/routes/${source}.js does not export handleRoute`);
    process.exit(1);
  }
  const ctx = { req: { query: (k) => params[k] } };
  const result = await handleRoute(ctx, false);
  console.log(JSON.stringify(result, null, 2));
  process.exit(0);
}

main().catch((e) => {
  console.error("Error:", e.message);
  process.exit(1);
});

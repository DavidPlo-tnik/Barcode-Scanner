// config.js — Marché Décarie scanner app config
// Keep this file separate so the GitHub token can be rotated without touching index.html.
//
// SETUP: create a GitHub fine-grained personal access token with:
//   - Repository access: ONLY DavidPlo-tnik/Barcode-Scanner
//   - Permissions: Contents -> Read and write
// Paste it below. If it ever leaks, revoke it in GitHub settings and generate a new one.
//
// This token can only edit files in THIS repo. It is used to save recipe text and
// photos to the recipes/ and images/ folders from the app.

window.DECARIE_CONFIG = {
  GH_OWNER: 'DavidPlo-tnik',
  GH_REPO:  'Barcode-Scanner',
  GH_BRANCH: 'main',
  // Paste the fine-grained token here (starts with github_pat_...)
  GH_TOKEN: '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',
};

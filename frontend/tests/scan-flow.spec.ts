import { test, expect } from "@playwright/test";

test("scan to patch preview flow", async ({ page }) => {
  await page.route("**/api/scan", async (route) => {
    await route.fulfill({ json: { scan_id: 11, status: "queued" } });
  });
  await page.route("**/api/status/11", async (route) => {
    await route.fulfill({ json: { scan_id: 11, status: "completed", progress: 100, logs: "done" } });
  });
  await page.route("**/api/results/11", async (route) => {
    await route.fulfill({
      json: [
        {
          id: 7,
          file: "/workspace/samples/python_yes_no/main.py",
          line_start: 8,
          line_end: 12,
          call_snippet: "client.chat.completions.create(...)",
          provider: "openai",
          inferred_intent: "yes_no_classification",
          rule_solvability_score: 0.93,
          confidence: 0.94,
          explanation: "Binary constrained output with explicit YES/NO instructions is highly deterministic.",
          risk_level: "low",
          estimated_api_calls_saved: 180,
          latency_improvement_ms: 320,
          fallback_behavior: "If deterministic rule fails validation, fall back to original AI call path.",
        },
      ],
    });
  });
  await page.route("**/api/patch/11/7", async (route) => {
    await route.fulfill({
      json: {
        candidate_id: 7,
        diff: "--- a\\n+++ b\\n@@ -1 +1 @@\\n-llm\\n+rule",
        explanation: "Patch replaces AI call with deterministic path.",
        risk_level: "low",
        tests_to_add: "Add parity test",
      },
    });
  });

  await page.goto("/");
  await expect(page.getByText("AI Call Optimizer")).toBeVisible();
  await page.getByRole("button", { name: "Run scan" }).click();
  await expect(page.getByText("yes_no_classification")).toBeVisible();
  await expect(page.getByText("Patch replaces AI call with deterministic path.")).toBeVisible();
});

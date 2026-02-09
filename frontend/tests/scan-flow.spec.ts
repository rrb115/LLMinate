import { test, expect } from "@playwright/test";

test("renders scan controls and patch panel", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("AI Call Optimizer")).toBeVisible();
  await expect(page.getByRole("button", { name: "Run scan" })).toBeVisible();
  await expect(page.getByText("Shadow Run")).toBeVisible();
});

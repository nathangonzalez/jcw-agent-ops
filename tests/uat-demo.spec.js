const { test, expect } = require("@playwright/test");

async function showStep(page, label, selector) {
  await page.evaluate(
    ({ label, selector }) => {
      const existing = document.getElementById("uat-step-label");
      if (existing) existing.remove();

      if (selector) {
        const target = document.querySelector(selector);
        if (target) {
          target.style.outline = "3px solid #e36f45";
          target.style.outlineOffset = "4px";
          target.setAttribute("data-uat-highlight", "true");
        }
      }

      document.querySelectorAll("[data-uat-highlight]").forEach((el) => {
        if (el.getAttribute("data-uat-highlight") === "true") return;
        el.style.outline = "";
      });

      const badge = document.createElement("div");
      badge.id = "uat-step-label";
      badge.textContent = label;
      badge.style.position = "fixed";
      badge.style.bottom = "24px";
      badge.style.left = "24px";
      badge.style.zIndex = "9999";
      badge.style.padding = "10px 14px";
      badge.style.borderRadius = "12px";
      badge.style.background = "#1f1a17";
      badge.style.color = "#fff";
      badge.style.fontFamily = "Palatino Linotype, Georgia, serif";
      badge.style.fontSize = "14px";
      badge.style.boxShadow = "0 10px 20px rgba(0,0,0,0.2)";
      document.body.appendChild(badge);
    },
    { label, selector }
  );
  await page.waitForTimeout(1200);
}

test("UAT demo: All Tasks UI walkthrough", async ({ page }) => {
  await page.goto("/");
  await showStep(page, "All Tasks dashboard loaded", ".hero");

  await showStep(page, "Filters panel", ".filters");
  await page.fill("#q", "test");
  await page.waitForTimeout(400);
  await page.fill("#q", "");

  await showStep(page, "New Task panel (not submitting)", "#toggle-add");
  await page.click("#toggle-add");
  await page.waitForTimeout(600);
  await page.fill("#new-title", "UAT Demo Task (not saved)");
  await page.fill("#new-tags", "uat,demo");
  await page.fill("#new-next", "Confirm UI behavior");
  await page.waitForTimeout(800);
  await page.click("#toggle-add");

  await showStep(page, "Task cards list", ".cards");

  const cards = await page.locator(".card").count();
  if (cards > 0) {
    await showStep(page, "Open Draft Email modal", ".card-actions button:nth-of-type(2)");
    await page.locator(".card-actions button", { hasText: "Draft Email" }).first().click();
    await page.waitForTimeout(600);
    await showStep(page, "Draft Email modal with approvals", "#draft-email");
    await page.click("#draft-close");
  } else {
    await showStep(page, "No tasks found in DB (verify data ingestion)", ".cards");
  }

  await showStep(page, "Sync Excel requires explicit APPROVE", "#sync-excel");
  await page.waitForTimeout(1000);

  await expect(page).toHaveTitle(/All Tasks/i);
});

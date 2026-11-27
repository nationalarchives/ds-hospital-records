import Cookies from "@nationalarchives/cookies";

export function initGlobalAlertDismissal(cookies) {
  const button = document.querySelector(".etna-global-alert__dismiss");
  if (!button) return;

  cookies ??= new Cookies();
  button.hidden = !cookies.preference("settings");
  cookies.on("changePreference", (preferences) => {
    if ("settings" in preferences) button.hidden = !preferences.settings;
  });
  button.addEventListener("click", () => {
    if (!cookies.preference("settings")) return;

    const cookieValues = document.cookie
      .split("; ")
      .filter((item) => item.startsWith("dismissed_notifications="))
      .map((item) => item.slice("dismissed_notifications=".length));
    const dismissed = new Map();
    for (const cookie of cookieValues) {
      try {
        const value = JSON.parse(decodeURIComponent(cookie));
        if (
          !Array.isArray(value) ||
          !value.every((id) => typeof id === "string" || Number.isSafeInteger(id))
        ) {
          throw new Error("Expected a list of notification IDs");
        }
        value.forEach((id) => dismissed.set(String(id), id));
      } catch (error) {
        console.warn("Invalid dismissed notifications cookie:", error);
      }
    }
    const previousDismissals = [...dismissed.values()];
    const id = button.value;
    const numericId = Number(id);
    dismissed.set(
      id,
      /^\d+$/.test(id) && Number.isSafeInteger(numericId) ? numericId : id,
    );
    for (const [key, value] of dismissed) {
      if (typeof value === "string" && /^\d+$/.test(value)) {
        const numericValue = Number(value);
        if (Number.isSafeInteger(numericValue)) dismissed.set(key, numericValue);
      }
    }

    document.cookie = "dismissed_notifications=; Path=/; Max-Age=0; SameSite=Lax";
    const cookieValue = JSON.stringify([...dismissed.values()]);
    cookies.set("dismissed_notifications", cookieValue, { session: true });
    if (cookies.get("dismissed_notifications") !== cookieValue) {
      if (previousDismissals.length) {
        document.cookie = `dismissed_notifications=${encodeURIComponent(JSON.stringify(previousDismissals))}; Path=/; SameSite=Lax`;
      }
      console.error("Failed to save dismissed notifications cookie.");
      return;
    }
    button.closest(".etna-global-alert").remove();
  });
}

"""Script de vérification du frontend via Playwright."""
from playwright.sync_api import sync_playwright
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

INDEX = "http://localhost:8000"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        errors = []
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ── 1. Chargement initial ──────────────────────────────────────────
        page.goto(INDEX)
        page.wait_for_selector(".stat-card", timeout=5000)
        stats = page.locator(".stat-value").all_text_contents()
        print(f"[1] Stats chargées : {stats}")
        page.screenshot(path="ss_01_dashboard.png")

        # ── 2. Cartes de tâches ───────────────────────────────────────────
        page.wait_for_selector(".task-card", timeout=5000)
        count = page.locator(".task-card").count()
        print(f"[2] {count} cartes affichées")
        page.screenshot(path="ss_02_cards.png")

        # ── 3. Créer une tâche ────────────────────────────────────────────
        page.click(".fab")
        page.wait_for_selector(".overlay.open", timeout=3000)
        page.fill("#fTitle", "Tâche de test frontend")
        page.fill("#fDesc", "Créée via Playwright")
        page.select_option("#fPriority", "high")
        page.fill("#fDueDate", "2026-12-31")
        # Tag
        page.click("#tagField")
        page.type("#tagField", "playwright")
        page.keyboard.press("Enter")
        page.type("#tagField", "test")
        page.keyboard.press("Enter")
        page.screenshot(path="ss_03_form.png")
        page.click(".btn-primary >> text=Enregistrer")
        page.wait_for_selector(".toast.success", timeout=4000)
        print("[3] Tâche créée — toast success visible")
        page.screenshot(path="ss_04_created.png")

        # ── 4. Recherche globale ──────────────────────────────────────────
        page.fill("#searchInput", "frontend")
        time.sleep(0.8)
        results = page.locator(".task-card").count()
        print(f"[4] Recherche 'frontend' → {results} résultat(s)")
        page.screenshot(path="ss_05_search.png")

        # ── 5. Recherche sans résultat ────────────────────────────────────
        page.fill("#searchInput", "xyzimpossible999")
        time.sleep(0.8)
        empty = page.locator(".empty-state").is_visible()
        print(f"[5] Recherche sans résultat → empty state : {empty}")
        page.screenshot(path="ss_06_empty.png")

        # ── 6. Filtres ────────────────────────────────────────────────────
        page.fill("#searchInput", "")
        time.sleep(0.5)
        page.click(".filter-btn[data-filter='overdue']")
        time.sleep(0.8)
        overdue_count = page.locator(".task-card").count()
        print(f"[6] Filtre 'En retard' → {overdue_count} tâche(s)")
        page.screenshot(path="ss_07_overdue.png")

        # ── 7. Marquer une tâche comme terminée ───────────────────────────
        page.click(".filter-btn[data-filter='all']")
        time.sleep(0.6)
        page.locator(".btn-icon.ok").first.click()
        page.wait_for_selector(".toast.success", timeout=4000)
        print("[7] Tâche marquée terminée — toast success")
        page.screenshot(path="ss_08_complete.png")

        # ── 8. Filtre 'Terminées' ─────────────────────────────────────────
        page.click(".filter-btn[data-filter='done']")
        time.sleep(0.6)
        done_count = page.locator(".task-card.done").count()
        print(f"[8] Filtre 'Terminées' → {done_count} tâche(s) done")
        page.screenshot(path="ss_09_done.png")

        # ── 9. Modifier une tâche ─────────────────────────────────────────
        page.click(".filter-btn[data-filter='all']")
        time.sleep(0.6)
        page.locator(".btn-icon >> text=✎").first.click()
        page.wait_for_selector(".overlay.open", timeout=3000)
        title_val = page.input_value("#fTitle")
        print(f"[9] Modal édition ouverte — titre : '{title_val}'")
        page.fill("#fTitle", title_val + " (modifiée)")
        page.click(".btn-primary >> text=Enregistrer")
        page.wait_for_selector(".toast.info", timeout=4000)
        print("[9] Modification enregistrée — toast info")
        page.screenshot(path="ss_10_edited.png")

        # ── 10. Tags cliquables dans le dashboard ─────────────────────────
        page.wait_for_selector(".tag-stat", timeout=3000)
        tag_el = page.locator(".tag-stat").first
        tag_name = tag_el.inner_text()
        tag_el.click()
        time.sleep(0.7)
        search_val = page.input_value("#searchInput")
        print(f"[10] Clic tag '{tag_name.strip()}' → searchInput='{search_val}'")
        page.screenshot(path="ss_11_tag_filter.png")

        # ── 11. Raccourci clavier N ───────────────────────────────────────
        page.fill("#searchInput", "")
        page.keyboard.press("Escape")
        page.evaluate("document.activeElement.blur()")  # retire le focus de l'input
        time.sleep(0.3)
        page.keyboard.press("n")
        modal_open = page.locator(".overlay.open").is_visible()
        print(f"[11] Raccourci 'N' → modal ouverte : {modal_open}")
        page.keyboard.press("Escape")
        page.screenshot(path="ss_12_shortcut.png")

        # ── Résumé ────────────────────────────────────────────────────────
        print(f"\nErreurs console JS : {errors if errors else 'aucune'}")
        browser.close()

if __name__ == "__main__":
    run()

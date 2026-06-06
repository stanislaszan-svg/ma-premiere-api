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

        # ── 2. Favicon ─────────────────────────────────────────────────────
        favicon = page.evaluate('''() => {
            const el = document.querySelector('link[rel="icon"]');
            return el ? el.href : null;
        }''')
        assert favicon and favicon.startswith("data:"), "Favicon manquant"
        print("[2] Favicon SVG inline : OK")

        # ── 3. Cartes de tâches ────────────────────────────────────────────
        page.wait_for_selector(".task-card", timeout=5000)
        count = page.locator(".task-card").count()
        print(f"[3] {count} cartes affichées")
        page.screenshot(path="ss_02_cards.png")

        # ── 4. Bouton header «Nouvelle tâche» ──────────────────────────────
        page.click("header .btn-primary")
        page.wait_for_selector(".overlay.open", timeout=3000)
        print("[4] Bouton header Nouvelle tâche : OK")
        page.keyboard.press("Escape")
        time.sleep(0.3)

        # ── 5. FAB + ───────────────────────────────────────────────────────
        page.click(".fab")
        page.wait_for_selector(".overlay.open", timeout=3000)
        print("[5] FAB + : OK")

        # ── 6. Créer une tâche ─────────────────────────────────────────────
        page.fill("#fTitle", "Tache de test frontend")
        page.fill("#fDesc", "Créée via Playwright")
        page.select_option("#fPriority", "high")
        page.fill("#fDueDate", "2026-12-31")
        page.click("#tagField")
        page.type("#tagField", "playwright")
        page.keyboard.press("Enter")
        page.type("#tagField", "test")
        page.keyboard.press("Enter")
        page.screenshot(path="ss_03_form.png")
        page.click(".modal-foot .btn-primary")
        page.wait_for_selector(".toast.success", timeout=4000)
        print("[6] Enregistrer (nouvelle tâche) : OK")
        page.screenshot(path="ss_04_created.png")
        time.sleep(0.8)

        # ── 7. Bouton Terminer ─────────────────────────────────────────────
        page.locator(".btn-icon[data-action=complete]").first.click()
        page.wait_for_selector(".toast.success", timeout=4000)
        print("[7] Bouton Terminer : OK")
        time.sleep(0.8)

        # ── 8. Bouton Rouvrir ──────────────────────────────────────────────
        page.click(".filter-btn[data-filter=done]")
        time.sleep(0.5)
        page.locator(".btn-icon[data-action=reopen]").first.click()
        page.wait_for_selector(".toast.info", timeout=4000)
        print("[8] Bouton Rouvrir : OK")
        time.sleep(0.8)

        # ── 9. Bouton Modifier + historique ───────────────────────────────
        page.click(".filter-btn[data-filter=all]")
        time.sleep(0.5)
        page.locator(".btn-icon[data-action=edit]").first.click()
        page.wait_for_selector(".overlay.open", timeout=3000)
        title_val = page.input_value("#fTitle")
        print(f"[9] Modal édition ouverte — titre : '{title_val}'")
        page.fill("#fTitle", title_val + " (modifiée)")
        page.click(".modal-foot .btn-primary")
        page.wait_for_selector(".toast.info", timeout=4000)
        print("[9] Modification enregistrée : OK")
        time.sleep(0.8)

        # ── 10. Historique dans le modal d'édition ─────────────────────────
        page.locator(".btn-icon[data-action=edit]").first.click()
        page.wait_for_selector(".overlay.open", timeout=3000)
        time.sleep(0.8)
        history_visible = page.locator("#historySection").is_visible()
        entry_count = page.locator(".history-entry").count()
        fields = page.locator(".history-field").all_text_contents()
        print(f"[10] Historique visible : {history_visible}, {entry_count} entrée(s), champs : {fields}")
        assert history_visible, "Section historique non visible"
        assert entry_count >= 2, "Pas assez d'entrées dans l'historique"
        page.screenshot(path="ss_10_history.png")
        page.keyboard.press("Escape")
        time.sleep(0.3)

        # ── 11. Bouton Supprimer ───────────────────────────────────────────
        page.evaluate("window.confirm = () => true")
        count_before = page.locator(".task-card").count()
        page.locator(".btn-icon[data-action=delete]").first.click()
        page.wait_for_selector(".toast.error", timeout=4000)
        count_after = page.locator(".task-card").count()
        print(f"[11] Bouton Supprimer : OK ({count_before} → {count_after} cartes)")
        time.sleep(0.8)

        # ── 12. Filtres ────────────────────────────────────────────────────
        for f in ["today", "upcoming", "overdue", "done", "all"]:
            page.click(f".filter-btn[data-filter={f}]")
            time.sleep(0.3)
        print("[12] Filtres (5) : OK")
        page.screenshot(path="ss_11_filters.png")

        # ── 13. Recherche globale ──────────────────────────────────────────
        page.fill("#searchInput", "frontend")
        time.sleep(0.8)
        results = page.locator(".task-card").count()
        print(f"[13] Recherche 'frontend' → {results} résultat(s)")
        page.screenshot(path="ss_12_search.png")

        # ── 14. Recherche sans résultat ────────────────────────────────────
        page.fill("#searchInput", "xyzimpossible999")
        time.sleep(0.8)
        empty = page.locator(".empty-state").is_visible()
        print(f"[14] Recherche sans résultat → empty state : {empty}")

        # ── 15. Tags cliquables dans le dashboard ──────────────────────────
        page.fill("#searchInput", "")
        time.sleep(0.5)
        page.wait_for_selector(".tag-stat", timeout=3000)
        tag_el = page.locator(".tag-stat").first
        tag_name = tag_el.get_attribute("data-tag")
        tag_el.click()
        time.sleep(0.5)
        search_val = page.input_value("#searchInput")
        print(f"[15] Tag '{tag_name}' cliquable → searchInput='{search_val}'")
        assert search_val == tag_name, "Tag click n'a pas mis à jour la recherche"
        page.screenshot(path="ss_13_tag_filter.png")

        # ── 16. Raccourci clavier N ────────────────────────────────────────
        page.fill("#searchInput", "")
        page.keyboard.press("Escape")
        page.evaluate("document.activeElement.blur()")
        time.sleep(0.3)
        page.keyboard.press("n")
        modal_open = page.locator(".overlay.open").is_visible()
        print(f"[16] Raccourci 'N' → modal ouverte : {modal_open}")
        page.keyboard.press("Escape")
        page.screenshot(path="ss_14_shortcut.png")

        # ── Résumé ─────────────────────────────────────────────────────────
        print(f"\nErreurs console JS : {errors if errors else 'aucune'}")
        browser.close()

if __name__ == "__main__":
    run()

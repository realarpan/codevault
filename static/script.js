const searchInput = document.getElementById("search");
const languageFilter = document.getElementById("language-filter");
const cards = Array.from(document.querySelectorAll(".snippet-card"));
const noResults = document.getElementById("no-results");
const languageCount = document.getElementById("language-count");

if (searchInput && languageFilter && languageCount) {
    const languages = [...new Set(cards.map(card => card.dataset.language))].sort();
    languages.forEach(language => {
        const option = document.createElement("option");
        option.value = language;
        option.textContent = language.charAt(0).toUpperCase() + language.slice(1);
        languageFilter.appendChild(option);
    });
    languageCount.textContent = languages.length;

    function filterSnippets() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const selectedLanguage = languageFilter.value;
        let visibleCount = 0;
        cards.forEach(card => {
            const visible = card.dataset.search.includes(searchTerm) &&
                (selectedLanguage === "all" || card.dataset.language === selectedLanguage);
            card.hidden = !visible;
            if (visible) visibleCount++;
        });
        if (noResults) noResults.hidden = visibleCount !== 0;
    }
    searchInput.addEventListener("input", filterSnippets);
    languageFilter.addEventListener("change", filterSnippets);
}

document.querySelectorAll(".copy-button").forEach(button => {
    button.addEventListener("click", async () => {
        const originalText = button.textContent;
        try {
            await navigator.clipboard.writeText(button.dataset.code || "");
            button.textContent = "Copied!";
        } catch (error) {
            button.textContent = "Copy failed";
        }
        window.setTimeout(() => { button.textContent = originalText; }, 1500);
    });
});

// Framer Motion powers the entrance choreography; the CSS remains a graceful fallback.
(async () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    try {
        const { animate, stagger } = await import("https://esm.sh/framer-motion@11.18.2");
        const intro = document.querySelector(".intro");
        const statCards = document.querySelectorAll(".stat-card");
        const snippetCards = document.querySelectorAll(".snippet-card");
        const formSection = document.querySelector(".form-section");
        if (intro) animate(intro, { opacity: [0, 1], y: [16, 0] }, { duration: .65, ease: [0.22, 1, 0.36, 1] });
        if (statCards.length) animate(statCards, { opacity: [0, 1], y: [14, 0] }, { duration: .48, delay: stagger(.08), ease: [0.22, 1, 0.36, 1] });
        if (snippetCards.length) animate(snippetCards, { opacity: [0, 1], y: [18, 0], scale: [.985, 1] }, { duration: .52, delay: stagger(.055), ease: [0.22, 1, 0.36, 1] });
        if (formSection) animate(formSection, { opacity: [0, 1], y: [18, 0] }, { duration: .6, delay: .18, ease: [0.22, 1, 0.36, 1] });
        const authCard = document.querySelector(".auth-card");
        if (authCard) animate(authCard, { opacity: [0, 1], y: [18, 0], scale: [.985, 1] }, { duration: .65, ease: [0.22, 1, 0.36, 1] });
    } catch (error) {
        document.documentElement.classList.add("motion-fallback");
    }
})();

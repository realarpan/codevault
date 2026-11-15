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
            const matchesSearch = card.dataset.search.includes(searchTerm);
            const matchesLanguage = selectedLanguage === "all" || card.dataset.language === selectedLanguage;
            const visible = matchesSearch && matchesLanguage;
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

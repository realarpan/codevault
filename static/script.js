const searchInput = document.getElementById("search");
const languageFilter = document.getElementById("language-filter");
const cards = Array.from(document.querySelectorAll(".snippet-card"));
const noResults = document.getElementById("no-results");
const languageCount = document.getElementById("language-count");

// Build the language filter from saved snippets.
const languages = [
    ...new Set(cards.map(card => card.dataset.language))
].sort();

languages.forEach(language => {
    const option = document.createElement("option");

    option.value = language;
    option.textContent =
        language.charAt(0).toUpperCase() + language.slice(1);

    languageFilter.appendChild(option);
});

languageCount.textContent = languages.length;

// Search and filter snippets.
function filterSnippets() {
    const searchTerm = searchInput.value.toLowerCase().trim();
    const selectedLanguage = languageFilter.value;

    let visibleCount = 0;

    cards.forEach(card => {
        const matchesSearch =
            card.dataset.search.includes(searchTerm);

        const matchesLanguage =
            selectedLanguage === "all" ||
            card.dataset.language === selectedLanguage;

        const visible = matchesSearch && matchesLanguage;

        card.hidden = !visible;

        if (visible) {
            visibleCount++;
        }
    });

    noResults.hidden = visibleCount !== 0;
}

searchInput.addEventListener("input", filterSnippets);
languageFilter.addEventListener("change", filterSnippets);

// Copy a snippet to the clipboard.
document.querySelectorAll(".copy-button").forEach(button => {
    button.addEventListener("click", async () => {
        const code = button.dataset.code;
        const originalText = button.textContent;

        try {
            await navigator.clipboard.writeText(code);
            button.textContent = "Copied!";

            setTimeout(() => {
                button.textContent = originalText;
            }, 1500);
        } catch (error) {
            button.textContent = "Copy failed";
        }
    });
});

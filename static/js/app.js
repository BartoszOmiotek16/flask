document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("search-form");
    const resultsDiv = document.getElementById("results");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        resultsDiv.innerHTML = "Loading...";

        const formData = new FormData(form);
        const query = formData.get("query");
        const max_pages = formData.get("max_pages");

        try {
            const response = await fetch("/search", {
                method: "POST",
                body: new URLSearchParams({ query, max_pages }),
            });

            const data = await response.json();
            resultsDiv.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        } catch (error) {
            resultsDiv.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
        }
    });
});

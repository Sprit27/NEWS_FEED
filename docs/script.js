async function loadNews() {
    try {
        // Fetch data from local news.json file
        const res = await fetch('./news.json');

        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }

        const newsData = await res.json();

        if (!newsData) {
            document.getElementById("news-container").innerHTML = "<p>No news data found.</p>";
            return;
        }

        // Update timestamp (you can modify this based on your needs)
        document.getElementById("updated").textContent =
            "Last updated: " + new Date().toLocaleString();

        renderNews(newsData);
    } catch (err) {
        console.error("Failed to load news:", err);
        console.error("Error details:", err.message);
        document.getElementById("news-container").innerHTML =
            `<p>⚠️ Failed to load news: ${err.message}</p>`;
    }
}

function renderNews(newsData) {
    const container = document.getElementById("news-container");
    container.innerHTML = "";

    Object.entries(newsData).forEach(([category, articles]) => {
        if (!articles.length) return;

        const section = document.createElement("div");
        section.className = "category";
        section.innerHTML = `<h2>${category}</h2>`;

        articles.forEach(article => {
            const div = document.createElement("div");
            div.className = "article";
            div.innerHTML = `
        <h3>${article.headline}</h3>
        <p>${article.summary}</p>
        <ul>${article.key_points.map(p => `<li>${p}</li>`).join("")}</ul>
      `;
            section.appendChild(div);
        });

        container.appendChild(section);
    });
}

loadNews();

// --- Dark Mode Toggle ---
const toggleBtn = document.getElementById('dark-mode-toggle');

function applyTheme(theme) {
    if (theme === 'dark') {
        document.body.classList.add('dark-mode');
        toggleBtn.textContent = "☀️";
    } else {
        document.body.classList.remove('dark-mode');
        toggleBtn.textContent = "🌙";
    }
}

// Load saved theme or default to dark
applyTheme(localStorage.getItem('theme') || 'dark');

// Toggle button
toggleBtn.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
    toggleBtn.textContent = isDark ? "☀️" : "🌙";
});

// --- Spinner stage updates ---
function updateSpinner(stage) {
    const loadingText = document.querySelector("#loading p");
    switch(stage) {
        case "fetching":
            loadingText.textContent = "📥 Fetching your Letterboxd watchlist...";
            break;
        case "processing":
            loadingText.textContent = "🔍 Processing your watchlist titles...";
            break;
        case "comparing":
            loadingText.textContent = "⚖️ Comparing your watchlist with YouTube free movies...";
            break;
        case "preparing":
            loadingText.textContent = "📊 Preparing results for display...";
            break;
        default:
            loadingText.textContent = "⏳ Loading...";
    }
}

// --- Render a results section ---
function renderSection(title, items, formatter, container) {
    const sectionHeader = document.createElement('h3');
    sectionHeader.textContent = title;
    container.appendChild(sectionHeader);

    if (items.length === 0) {
        const none = document.createElement('p');
        none.textContent = "None found.";
        container.appendChild(none);
        return;
    }

    const ul = document.createElement('ul');
    items.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = formatter(item);
        ul.appendChild(li);
    });
    container.appendChild(ul);
}

// --- Main form submit handler ---
document.getElementById('watchlist-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const username = document.getElementById('username').value.trim();
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const errorDiv = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    const movieList = document.getElementById('movie-list');

    // Reset previous state
    resultsDiv.classList.add('hidden');
    errorDiv.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    movieList.innerHTML = '';
    errorMessage.textContent = '';

    if (!username) {
        loadingDiv.classList.add('hidden');
        errorMessage.innerHTML = "❌ Please enter your <a href='https://letterboxd.com/' target='_blank'>Letterboxd</a> username before comparing.";
        errorDiv.classList.remove('hidden');
        return;
    }

    loadingDiv.classList.remove('hidden');
    updateSpinner("fetching");

    try {
        const response = await fetch('/compare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username })
        });

        // Stage: processing
        updateSpinner("processing");
        const data = await response.json();

        if (data.empty_watchlist) {
            loadingDiv.classList.add('hidden');
            errorMessage.innerHTML = `📭 Your watchlist seems to be empty. <a href="https://mashable.com/article/how-to-add-a-movie-to-your-watchlist-on-letterboxd" target="_blank">Add movies to it</a> instead?`;
            errorDiv.classList.remove('hidden');
            return;
        }

        if (!response.ok) {
            loadingDiv.classList.add('hidden');
            errorMessage.textContent = data.error || "❌ An unknown error occurred.";
            errorDiv.classList.remove('hidden');
            console.error('Error:', data.error);
            return;
        }

        // Stage: comparing
        updateSpinner("comparing");

        // Stage: preparing
        updateSpinner("preparing");

        // Render results
        if (data.matches.length > 0) {
            renderSection("✅ Matches", data.matches, movie =>
                `${movie.yt_title} (${movie.yt_year}) — <a href="${movie.yt_href}" target="_blank">YouTube</a> | <a href="${movie.lb_url}" target="_blank">Letterboxd</a>`,
                movieList
            );
        } else {
            const noMatchMsg = document.createElement('p');
            noMatchMsg.innerHTML = `📭 No matches found! Check out the <a href="https://www.youtube.com/feed/storefront/" target="_blank">selection of free movies on YouTube</a>.`;
            movieList.appendChild(noMatchMsg);
        }

        // Only render Ambiguous Matches if there are any
        if (data.ambiguous_matches.length > 0) {
            // Optional example header
            const ambiguousHeader = document.createElement('p');
            ambiguousHeader.innerHTML = "Example: Red Eye (2005) — horror on a train vs. Red Eye — thriller on a plane";
            movieList.appendChild(ambiguousHeader);

            renderSection("⚠️ Ambiguous Matches", data.ambiguous_matches, movie =>
                `${movie.yt_title} (${movie.yt_year}) — <a href="${movie.yt_href}" target="_blank">YouTube</a> | <a href="${movie.lb_url}" target="_blank">Letterboxd</a> [${movie.note}]`,
                movieList
            );
        }

        // Only render Near Misses if there are any
        if (data.near_misses.length > 0) {
            renderSection("❓ Near Misses", data.near_misses, movie =>
                `${movie.yt_title} (${movie.yt_year || "?"}) — <a href="${movie.yt_href}" target="_blank">YouTube</a> | <a href="${movie.lb_url}" target="_blank">Letterboxd</a> [${movie.reason}]`,
                movieList
            );
        }

        loadingDiv.classList.add('hidden');
        resultsDiv.classList.remove('hidden');

    } catch (error) {
        loadingDiv.classList.add('hidden');
        errorMessage.textContent = "⚠️ Network error. Please try again later.";
        errorDiv.classList.remove('hidden');
        console.error('Network error:', error);
    } finally {
        loadingDiv.classList.add('hidden');
    }
});

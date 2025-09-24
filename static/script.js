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
            loadingText.textContent = "📥 Hang tight! Fetching your Letterboxd data...";
            break;
        case "gettingwatched":
            loadingText.textContent = "📥 Fetching your logged films on Letterboxd...";
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

function renderSection(title, items, renderItem, container, isHtml = false) {
    if (!items || items.length === 0) return;

    const list = document.createElement("ul");
    items.forEach(item => {
        const li = document.createElement("li");
        li.innerHTML = renderItem(item);
        list.appendChild(li);
    });

    container.appendChild(list);
}

// --- Render a movie results section ---
function renderMovieResults(title, sectionData, container, username) {
    const baseUrl = `https://letterboxd.com/${username}`;
    const sectionUrl = title.toLowerCase().includes("watchlist")
        ? `${baseUrl}/watchlist/`
        : `${baseUrl}/films/`;

    // --- Matches ---
    const matches = sectionData.matches?.length || 0;
    
    // If no matches, don't render anything at all
    if (matches === 0) return;

    let matchTitle = "";
    if (matches === 1) {
        matchTitle = `1 match from your <a href="${sectionUrl}" target="_blank">${title}</a>`;
    } else {
        matchTitle = `${matches} matches from your <a href="${sectionUrl}" target="_blank">${title}</a>`;
    }

    const header = document.createElement("h3");
    header.style.display = "flex";
    header.style.justifyContent = "space-between";
    header.style.alignItems = "center";
    const titleSpan = document.createElement("span"); // add titlespan to hold HTML for the flexbox
    titleSpan.innerHTML = matchTitle; // keep your HTML links
    header.appendChild(titleSpan);

    // Copy button
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = '📋 Copy';
    copyBtn.style.marginLeft = '1rem';
    copyBtn.style.cursor = 'pointer';
    copyBtn.addEventListener('click', () => {
        const textToCopy = sectionData.matches.map(
            m => `${m.yt_title} (${m.yt_year}) — ${m.yt_href}`
            ).join('\n');
            navigator.clipboard.writeText(textToCopy);
            copyBtn.textContent = 'Copied to Clipboard! ✅';
            setTimeout(() => (copyBtn.textContent = '📋 Copy'), 2000);
    });
    header.appendChild(copyBtn);
    container.appendChild(header);

    renderSection(
        matchTitle,
        sectionData.matches,
        movie =>
            `${movie.yt_title} (${movie.yt_year}) — <a href="${movie.yt_href}" target="_blank">YouTube</a>` +
            (movie.lb_url ? ` | <a href="${movie.lb_url}" target="_blank">Letterboxd</a>` : ''),
        container,
        true // flag to say we’re passing HTML, not plain text
    );

    // --- Ambiguous Matches ---
    const ambiguousCount = sectionData.ambiguous_matches?.length || 0;
    if (ambiguousCount > 0) {
        const ambiguousTitle =
            ambiguousCount === 1
                ? `1 ambiguous match from your <a href="${sectionUrl}" target="_blank">${title}</a>`
                : `${ambiguousCount} ambiguous matches from your <a href="${sectionUrl}" target="_blank">${title}</a>`;

        renderSection(
            ambiguousTitle,
            sectionData.ambiguous_matches,
            movie =>
                `${movie.yt_title} (${movie.yt_year}) — <a href="${movie.yt_href}" target="_blank">YouTube</a>` +
                (movie.lb_url ? ` | <a href="${movie.lb_url}" target="_blank">Letterboxd</a>` : '') +
                ` [${movie.note}]`,
            container,
            true
        );
    }

    // --- Near Misses ---
    const nearMissCount = sectionData.near_misses?.length || 0;
    if (nearMissCount > 0) {
        const nearMissTitle =
            nearMissCount === 1
                ? `1 near miss from your <a href="${sectionUrl}" target="_blank">${title}</a>`
                : `${nearMissCount} near misses from your <a href="${sectionUrl}" target="_blank">${title}</a>`;

        renderSection(
            nearMissTitle,
            sectionData.near_misses,
            movie =>
                `${movie.yt_title} (${movie.yt_year || "?"}) — <a href="${movie.yt_href}" target="_blank">YouTube</a>` +
                (movie.lb_url ? ` | <a href="${movie.lb_url}" target="_blank">Letterboxd</a>` : '') +
                ` [${movie.reason}]`,
            container,
            true
        );
    }
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

        // }
        renderMovieResults("watchlist", data.watchlist, movieList, data.username);
        renderMovieResults("logged films", data.watched, movieList, data.username);

        // Optionally, show a "No matches" message if both sections are empty
        if (
            (!data.watchlist.matches || data.watchlist.matches.length === 0) &&
            (!data.watched.matches || data.watched.matches.length === 0)
        ) {
            const noMatchMsg = document.createElement('p');
            noMatchMsg.innerHTML = `📭 No matches found! Check out the selection of <a href="https://www.youtube.com/feed/storefront/" target="_blank">free movies on YouTube</a> & log some more movies on your <a href="https://letterboxd.com/${data.username}" target="_blank">Letterboxd</a>!`;
            movieList.appendChild(noMatchMsg);
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

(async () => {
  const seen = new Map();
  let lastHeight = 0, stagnant = 0;
  const wait = ms => new Promise(r => setTimeout(r, ms));

  const cleanYouTubeUrl = url => {
    try {
      const u = new URL(url, location.origin);
      const vid = u.searchParams.get('v');
      return vid ? `https://www.youtube.com/watch?v=${vid}` : url;
    } catch {
      return url;
    }
  };

  while (stagnant < 3) {
    window.scrollTo(0, document.documentElement.scrollHeight);
    await wait(1200);

    document.querySelectorAll('ytd-badge-supported-renderer').forEach(badge => {
      const label = ((badge.textContent || '') + ' ' + (badge.getAttribute('aria-label') || '')).toLowerCase();
      if (!label.includes('free with ads')) return;

      const card = badge.closest('ytd-grid-movie-renderer, ytd-video-renderer, ytd-rich-item-renderer');
      if (!card) return;

      const linkEl = card.querySelector('a[href^="/watch"], a#thumbnail');
      if (!linkEl) return;

      const cleanHref = cleanYouTubeUrl(linkEl.href || linkEl.getAttribute('href'));
      const vid  = cleanHref.includes('/watch') ? (new URL(cleanHref)).searchParams.get('v') : cleanHref;
      if (seen.has(vid)) return;

      const titleEl = card.querySelector(
        'a#video-title, yt-formatted-string#video-title, a#video-title-link, #video-title, #title a'
      );
      const title = titleEl ? (titleEl.textContent.trim() || titleEl.getAttribute('title') || titleEl.getAttribute('aria-label') || '') : '';

      // Extract year from metadata
      let year = null;
      const metadataEl = card.querySelector('span.grid-movie-renderer-metadata');
      if (metadataEl) {
          const match = metadataEl.textContent.match(/\b(19|20)\d{2}\b/);
          if (match) year = parseInt(match[0]);
      }

      seen.set(vid, { title, year, href: cleanHref });
    });

    const h = document.documentElement.scrollHeight;
    if (h === lastHeight) stagnant++;
    else { stagnant = 0; lastHeight = h; }
  }

  console.log(`Found ${seen.size} Free with Ads movies`);
  console.table([...seen.values()]);

  // Export as JSON
  const jsonBlob = new Blob([JSON.stringify([...seen.values()], null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(jsonBlob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'youtube_free_with_ads.json';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
})();

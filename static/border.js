// ===== Marquee & Spotlight Setup =====
const spotlight = document.querySelector('.spotlight');
let mouseX = 0, mouseY = 0;
let currentX = 0, currentY = 0;

// Track cursor anywhere on the page
document.addEventListener('mousemove', (e) => {
  mouseX = e.clientX;
  mouseY = e.clientY;
});

// Animate spotlight smoothly
function animateSpotlight() {
  currentX += (mouseX - currentX) * 0.2;
  currentY += (mouseY - currentY) * 0.2;

  spotlight.style.left = `${currentX}px`;
  spotlight.style.top = `${currentY}px`;

  requestAnimationFrame(animateSpotlight);
}

animateSpotlight();

const bulbs = ['🟡','⚪'];
const bulbSpacing = 2; // spaces between bulbs
const numBulbs = 50;   // how many bulbs across top/bottom

function makeRow(startIndex, count) {
  let row = '';
  for (let i = 0; i < count; i++) {
    row += bulbs[(i + startIndex) % 2] + ' '.repeat(bulbSpacing);
  }
  return row;
}

function updateBorders(tick) {
  const container = document.querySelector('.container');

  const tempSpan = document.createElement('span');
  tempSpan.textContent = '🟡';
  tempSpan.style.visibility = 'hidden';
  document.body.appendChild(tempSpan);

  const bulbWidth = tempSpan.offsetWidth;
  const bulbHeight = tempSpan.offsetHeight;

  document.body.removeChild(tempSpan);

  const topCount = Math.floor(container.clientWidth / bulbWidth);
  const sideCount = Math.floor(container.clientHeight / bulbHeight);

  const top = document.querySelector('.marquee-border.top');
  const bottom = document.querySelector('.marquee-border.bottom');
  top.innerHTML = '';
  bottom.innerHTML = '';

  for (let i = 0; i < topCount; i++) {
    const bulbTop = document.createElement('span');
    bulbTop.textContent = bulbs[(i + tick) % 2];
    top.appendChild(bulbTop);

    const bulbBottom = document.createElement('span');
    bulbBottom.textContent = bulbs[(i + tick + 1) % 2];
    bottom.appendChild(bulbBottom);
  }

  const left = document.querySelector('.marquee-border.left');
  const right = document.querySelector('.marquee-border.right');
  left.innerHTML = '';
  right.innerHTML = '';

  for (let i = 0; i < sideCount; i++) {
    const bulbLeft = document.createElement('div');
    bulbLeft.textContent = bulbs[(i + tick) % 2];
    left.appendChild(bulbLeft);

    const bulbRight = document.createElement('div');
    bulbRight.textContent = bulbs[(i + tick + 1) % 2];
    right.appendChild(bulbRight);
  }
}

let tick = 0;
setInterval(() => {
  updateBorders(tick);
  window.addEventListener('resize', () => updateBorders(tick));
  tick = (tick + 1) % 2; // flip back and forth
}, 500); // speed (ms)

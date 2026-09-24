// Apple Configurator Option Chips Switching
document.querySelectorAll('.configurator-chip').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.configurator-chip').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.config-panel').forEach(panel => panel.classList.remove('active'));

    button.classList.add('active');
    const targetId = button.getAttribute('data-target');
    const targetPanel = document.getElementById(targetId);
    if (targetPanel) {
      targetPanel.classList.add('active');
    }
  });
});

// FAQ Accordion
document.querySelectorAll('.faq-trigger').forEach(button => {
  button.addEventListener('click', () => {
    const row = button.parentElement;
    row.classList.toggle('open');
  });
});

// Copy Code Button
function copySnippet(btn) {
  const codeBox = btn.closest('.code-chassis');
  const code = codeBox.querySelector('code').innerText;
  navigator.clipboard.writeText(code).then(() => {
    const originalText = btn.innerText;
    btn.innerText = 'Copied';
    btn.style.backgroundColor = '#0066cc';
    setTimeout(() => {
      btn.innerText = originalText;
      btn.style.backgroundColor = '';
    }, 2000);
  });
}

// Live Terminal Upload Telemetry Animation
const queueFiles = [
  { name: 'IMG_2026_0918.jpg', size: '3.4M', speed: '3.2MB/s' },
  { name: 'PXL_VACATION_4K.mp4', size: '142M', speed: '7.8MB/s' },
  { name: 'DSC_NIGHT_RAW.jpg', size: '4.1M', speed: '3.1MB/s' },
  { name: 'TRIP_DOCUMENTARY.mkv', size: '1.2G', speed: '8.4MB/s' }
];

let qIdx = 0;
let qPercent = 30;
let qBase = 3483;

setInterval(() => {
  const fileEl = document.getElementById('term-file');
  const meterEl = document.getElementById('term-meter');
  const countEl = document.querySelector('.tv-count');
  if (!fileEl || !meterEl) return;

  qPercent += 20;
  if (qPercent >= 100) {
    qPercent = 100;
    const cur = queueFiles[qIdx % queueFiles.length];
    meterEl.innerText = `100%|██████████| ${cur.size}/${cur.size} [00:01, ${cur.speed}] - Done!`;

    setTimeout(() => {
      qPercent = 15;
      qBase++;
      qIdx++;
      const next = queueFiles[qIdx % queueFiles.length];
      if (countEl) countEl.innerText = `[${qBase}/5242]`;
      fileEl.innerText = next.name + ':';
      meterEl.innerText = `${qPercent}%|██        | ...`;
    }, 700);
  } else {
    const cur = queueFiles[qIdx % queueFiles.length];
    const barsCount = Math.floor(qPercent / 10);
    const bars = '█'.repeat(barsCount) + ' '.repeat(10 - barsCount);
    meterEl.innerText = `${qPercent}%|${bars}| ... [${cur.speed}]`;
  }
}, 550);

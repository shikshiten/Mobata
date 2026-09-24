// Tab Switching
document.querySelectorAll('.tab-btn').forEach(button => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

    button.classList.add('active');
    const targetId = 'tab-' + button.getAttribute('data-tab');
    const targetPane = document.getElementById(targetId);
    if (targetPane) {
      targetPane.classList.add('active');
    }
  });
});

// FAQ Accordion
document.querySelectorAll('.faq-question').forEach(button => {
  button.addEventListener('click', () => {
    const item = button.parentElement;
    item.classList.toggle('open');
  });
});

// Copy Code Button
function copyCode(btn) {
  const codeBox = btn.closest('.code-box');
  const code = codeBox.querySelector('code').innerText;
  navigator.clipboard.writeText(code).then(() => {
    const originalText = btn.innerText;
    btn.innerText = 'Copied!';
    btn.style.color = '#10b981';
    setTimeout(() => {
      btn.innerText = originalText;
      btn.style.color = '';
    }, 2000);
  });
}

// Simulated Terminal Upload Animation
const sampleFiles = [
  { name: 'IMG_2026_0918.jpg', size: '3.4M', speed: '3.2MB/s' },
  { name: 'PXL_VACATION_01.jpg', size: '2.8M', speed: '3.6MB/s' },
  { name: 'VID_4K_BEACH.mp4', size: '142M', speed: '7.8MB/s' },
  { name: 'NIGHT_SKY_RAW.jpg', size: '4.1M', speed: '3.1MB/s' }
];

let fileIdx = 0;
let percent = 20;
let baseCount = 3483;

setInterval(() => {
  const activeFileEl = document.getElementById('term-active-file');
  const barEl = document.getElementById('term-bar');
  if (!activeFileEl || !barEl) return;

  percent += 25;
  if (percent >= 100) {
    percent = 100;
    const cur = sampleFiles[fileIdx % sampleFiles.length];
    barEl.innerHTML = `100%|██████████| ${cur.size}/${cur.size} [00:01, ${cur.speed}] - Done!`;
    
    // Switch to next file
    setTimeout(() => {
      percent = 15;
      baseCount++;
      fileIdx++;
      const next = sampleFiles[fileIdx % sampleFiles.length];
      const prefix = document.querySelector('.cursor-line .c-cyan');
      if (prefix) prefix.innerText = `[${baseCount}/5242]`;
      activeFileEl.innerText = next.name + ':';
      barEl.innerText = `${percent}%|██        | ...`;
    }, 800);
  } else {
    const cur = sampleFiles[fileIdx % sampleFiles.length];
    const barsCount = Math.floor(percent / 10);
    const bars = '█'.repeat(barsCount) + ' '.repeat(10 - barsCount);
    barEl.innerText = `${percent}%|${bars}| ... [${cur.speed}]`;
  }
}, 600);

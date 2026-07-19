(() => {
  const PLANE_WIDTH = 1400;
  const PLANE_HEIGHT = 820;
  const tips = [
    'If you are having trouble understanding any words or phrases in the story, you can highlight that part and click the question mark icon.',
    'Everything you look up is kept in the notebook beside the story, so you can go back to it whenever you like.',
    'When the story ends, your looked-up phrases become a short vocabulary review.'
  ];
  const dots = [...document.querySelectorAll('#loadingDots button')];
  const slides = [...document.querySelectorAll('.tutorial-card')];
  const tip = document.querySelector('#loadingTip');
  const rail = document.querySelector('#loadingRail');
  const label = document.querySelector('#loadingLabel');
  const start = document.querySelector('#loadingStart');
  let activeSlide = 0;
  let isReady = false;

  const solve = (matrix) => {
    const rows = matrix.length;
    const columns = matrix[0].length;
    for (let column = 0; column < rows; column += 1) {
      let pivot = column;
      for (let row = column + 1; row < rows; row += 1) if (Math.abs(matrix[row][column]) > Math.abs(matrix[pivot][column])) pivot = row;
      [matrix[column], matrix[pivot]] = [matrix[pivot], matrix[column]];
      const divisor = matrix[column][column];
      if (Math.abs(divisor) < 1e-10) throw new Error('Perspective plane could not be solved.');
      for (let c = column; c < columns; c += 1) matrix[column][c] /= divisor;
      for (let row = 0; row < rows; row += 1) {
        if (row === column) continue;
        const factor = matrix[row][column];
        for (let c = column; c < columns; c += 1) matrix[row][c] -= factor * matrix[column][c];
      }
    }
    return matrix.map((row) => row[columns - 1]);
  };

  const homography = (from, to) => solve(from.flatMap(([x, y], index) => {
    const [u, v] = to[index];
    return [[x, y, 1, 0, 0, 0, -x * u, -y * u, u], [0, 0, 0, x, y, 1, -x * v, -y * v, v]];
  }));

  const cssMatrix = ([h11, h12, h13, h21, h22, h23, h31, h32]) => `matrix3d(${[h11, h21, 0, h31, h12, h22, 0, h32, 0, 0, 1, 0, h13, h23, 0, 1].join(',')})`;

  const pinSheetToBook = () => {
    const stage = document.querySelector('.loading-carousel-stage');
    const sheet = document.querySelector('#loadingSheetPlane');
    if (!stage || !sheet || window.matchMedia('(max-width: 700px)').matches) return;
    const width = stage.clientWidth;
    const height = stage.clientHeight;
    // Clockwise book-page corners: bottom edge deliberately follows the cover rim.
    const target = [[.157 * width, .065 * height], [.818 * width, .078 * height], [.886 * width, .852 * height], [.083 * width, .839 * height]];
    const source = [[0, 0], [PLANE_WIDTH, 0], [PLANE_WIDTH, PLANE_HEIGHT], [0, PLANE_HEIGHT]];
    sheet.style.transform = cssMatrix(homography(source, target));
    sheet.dataset.quad = target.flat().map((value) => Math.round(value)).join(',');
    sheet.classList.add('is-ready');
  };

  const placeStartButton = () => {
    const stage = document.querySelector('.loading-carousel-stage');
    const status = document.querySelector('.loading-status');
    if (!stage || !status || !start) return;
    const stageBox = stage.getBoundingClientRect();
    const statusBox = status.getBoundingClientRect();
    start.style.left = `${statusBox.left - stageBox.left + statusBox.width / 2}px`;
    start.style.top = `${statusBox.bottom - stageBox.top + 26}px`;
  };

  const selectSlide = (index) => {
    activeSlide = index;
    dots.forEach((dot, i) => { dot.classList.toggle('is-current', i === index); dot.setAttribute('aria-pressed', String(i === index)); });
    slides.forEach((slide, i) => slide.classList.toggle('is-active', i === index));
    tip.textContent = tips[index];
    window.requestAnimationFrame(placeStartButton);
  };
  dots.forEach((dot, index) => dot.addEventListener('click', () => selectSlide(index)));

  const slideTimer = window.setInterval(() => {
    if (!isReady) selectSlide((activeSlide + 1) % slides.length);
  }, 900);

  const milestones = [[18, 'Setting the scene...'], [47, 'Gathering your guide...'], [76, 'Opening the first page...'], [100, 'Your story is ready.']];
  milestones.forEach(([progress, text], index) => setTimeout(() => {
    rail.style.width = `${progress}%`;
    label.textContent = text;
    window.requestAnimationFrame(placeStartButton);
    if (index === milestones.length - 1) {
      isReady = true;
      window.clearInterval(slideTimer);
      label.textContent = 'Your story is ready.';
      start.setAttribute('aria-disabled', 'false');
    }
  }, index * 800 + 250));

  // The responsive mockup uses the stable CSS plane until a viewport-aware
  // four-corner calibration is available.
  placeStartButton();
  window.addEventListener('resize', placeStartButton, { passive: true });
})();

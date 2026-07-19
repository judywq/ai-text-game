(function () {
  var BASE_WIDTH = 1600;
  var BASE_HEIGHT = 900;
  var PAGE_WIDTH = 560;
  var PAGE_HEIGHT = 600;
  var initialDevicePixelRatio = window.devicePixelRatio || 1;

  // Local tangent plane of the usable writing area, clockwise from top-left.
  // The illustrated page rim bows upward toward the gutter, so mapping to the
  // full corner-to-corner chord makes HTML look too level. These points follow
  // the approximately seven-degree tangent marked by the page's upper rim.
  var target = [
    [265, 170],
    [755, 110],
    [840, 665],
    [275, 725]
  ];

  var source = [
    [0, 0],
    [PAGE_WIDTH, 0],
    [PAGE_WIDTH, PAGE_HEIGHT],
    [0, PAGE_HEIGHT]
  ];

  function solve(matrix) {
    var rows = matrix.length;
    var cols = matrix[0].length;

    for (var column = 0; column < rows; column += 1) {
      var pivot = column;
      for (var row = column + 1; row < rows; row += 1) {
        if (Math.abs(matrix[row][column]) > Math.abs(matrix[pivot][column])) pivot = row;
      }

      var swap = matrix[column];
      matrix[column] = matrix[pivot];
      matrix[pivot] = swap;

      var divisor = matrix[column][column];
      if (Math.abs(divisor) < 1e-10) throw new Error("Perspective plane could not be solved.");
      for (var c = column; c < cols; c += 1) matrix[column][c] /= divisor;

      for (var r = 0; r < rows; r += 1) {
        if (r === column) continue;
        var factor = matrix[r][column];
        for (var k = column; k < cols; k += 1) matrix[r][k] -= factor * matrix[column][k];
      }
    }

    return matrix.map(function (row) { return row[cols - 1]; });
  }

  function homography(from, to) {
    var equations = [];

    for (var i = 0; i < 4; i += 1) {
      var x = from[i][0];
      var y = from[i][1];
      var u = to[i][0];
      var v = to[i][1];

      equations.push([x, y, 1, 0, 0, 0, -x * u, -y * u, u]);
      equations.push([0, 0, 0, x, y, 1, -x * v, -y * v, v]);
    }

    return solve(equations);
  }

  function cssMatrix(values) {
    var h11 = values[0];
    var h12 = values[1];
    var h13 = values[2];
    var h21 = values[3];
    var h22 = values[4];
    var h23 = values[5];
    var h31 = values[6];
    var h32 = values[7];

    return "matrix3d(" + [
      h11, h21, 0, h31,
      h12, h22, 0, h32,
      0, 0, 1, 0,
      h13, h23, 0, 1
    ].join(",") + ")";
  }

  function sizeScene() {
    var scene = document.querySelector(".scene");
    var stage = document.getElementById("sceneStage");
    if (!scene || !stage || window.matchMedia("(max-width: 560px)").matches) return;

    /* Preserve the normal-size composition while zooming in so the browser
       exposes a real pannable scene. Zooming out is allowed to re-cover the
       larger CSS viewport, preventing empty gutters around the artwork. */
    if ((window.devicePixelRatio || 1) > initialDevicePixelRatio + 0.01) return;
    var scale = Math.max(scene.clientWidth / BASE_WIDTH, scene.clientHeight / BASE_HEIGHT);
    document.documentElement.style.setProperty("--scene-scale", scale.toFixed(5));
    stage.style.width = Math.ceil(BASE_WIDTH * scale) + "px";
    stage.style.height = Math.ceil(BASE_HEIGHT * scale) + "px";

    window.requestAnimationFrame(function () {
      scene.scrollLeft = Math.max(0, (scene.scrollWidth - scene.clientWidth) / 2);
      scene.scrollTop = Math.max(0, (scene.scrollHeight - scene.clientHeight) / 2);
    });
  }

  function updatePanMode() {
    var scene = document.querySelector(".scene");
    if (!scene || window.matchMedia("(max-width: 560px)").matches) return;

    var deviceZoomed = (window.devicePixelRatio || 1) > initialDevicePixelRatio + 0.01;
    scene.classList.toggle("is-pannable", deviceZoomed);
  }

  function init() {
    var plane = document.getElementById("pagePlane");
    if (!plane) return;

    plane.style.transform = cssMatrix(homography(source, target));
    plane.dataset.quad = target.flat().join(",");
    plane.classList.add("is-ready");
    sizeScene();
    updatePanMode();

    if (new URLSearchParams(window.location.search).has("debug")) {
      document.body.classList.add("debug");
    }
  }

  window.addEventListener("resize", function () {
    updatePanMode();
    sizeScene();
  }, { passive: true });
  window.addEventListener("DOMContentLoaded", init);
})();

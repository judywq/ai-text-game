(function () {
  var BASE_WIDTH = 1672;
  // assets/signup-page.png is 1672x941 and carries a baked 81px header band
  // plus a footer band. The canvas clips to the book region, so the plate is
  // offset by -81px in CSS and every coordinate below is canvas-relative.
  var BASE_HEIGHT = 808;
  var PLANE_WIDTH = 448;
  var PLANE_HEIGHT = 590;   // 448/590 = 0.759, the frame's measured aspect
  var initialDevicePixelRatio = window.devicePixelRatio || 1;

  // Calibrated live writing plane on the right (blank) page, clockwise from
  // top-left. Derived by fitting lines to the four inner gold rules of the
  // frame (sub-pixel dip tracking), then intersecting them:
  //   top    y = 0.0541x + 82.6      bottom y = 0.0081x + 801.3
  //   left   x = 0.0300y + 866.5     right  x = 0.1016y + 1338.2
  // The top rule descends toward the outer edge (+3.1 deg) while the bottom
  // is nearly level (+0.5 deg); that convergence is the page's perspective,
  // so page-horizontal rows must be drawn with progressively shallower tilt.
  // Verified by inverse-mapping the reference artwork's printed Sign Up
  // button through this plane: it returns a level rectangle (dv < 0.003).
  // Recalibrate if assets/signup-page.png is replaced.
  var target = [
    [870, 49],
    [1354, 75],
    [1421, 732],
    [891, 727]
  ];

  var source = [
    [0, 0],
    [PLANE_WIDTH, 0],
    [PLANE_WIDTH, PLANE_HEIGHT],
    [0, PLANE_HEIGHT]
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
      if (Math.abs(divisor) < 1e-10) throw new Error("Signup perspective plane could not be solved.");
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
    return "matrix3d(" + [
      values[0], values[3], 0, values[6],
      values[1], values[4], 0, values[7],
      0, 0, 1, 0,
      values[2], values[5], 0, 1
    ].join(",") + ")";
  }

  function sizeScene() {
    var scene = document.querySelector(".signup-scene");
    var stage = document.getElementById("signupSceneStage");
    if (!scene || !stage || window.matchMedia("(max-width: 560px)").matches) return;

    /* A zoom-in keeps the calibrated book at its normal scale and lets the
       user pan it; zoom-out recomputes a cover scale so no bare background
       becomes visible. */
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
    var scene = document.querySelector(".signup-scene");
    if (!scene || window.matchMedia("(max-width: 560px)").matches) return;
    var deviceZoomed = (window.devicePixelRatio || 1) > initialDevicePixelRatio + 0.01;
    scene.classList.toggle("is-pannable", deviceZoomed);
  }

  function bindToggle(button) {
    var field = document.getElementById(button.getAttribute("aria-controls"));
    if (!field) return;
    button.addEventListener("click", function () {
      var reveal = field.type === "password";
      field.type = reveal ? "text" : "password";
      button.textContent = reveal ? "Hide" : "Show";
      button.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
    });
  }

  function init() {
    var plane = document.getElementById("signupPlane");
    if (!plane) return;
    plane.style.transform = cssMatrix(homography(source, target));
    plane.dataset.quad = target.flat().join(",");
    plane.classList.add("is-ready");
    sizeScene();
    updatePanMode();
    document.querySelectorAll(".password-toggle").forEach(bindToggle);
  }

  window.addEventListener("resize", function () {
    updatePanMode();
    sizeScene();
  }, { passive: true });
  window.addEventListener("DOMContentLoaded", init);
})();

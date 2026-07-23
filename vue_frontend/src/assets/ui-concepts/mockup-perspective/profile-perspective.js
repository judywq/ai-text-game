(function () {
  var BASE_WIDTH = 1672;
  var BASE_HEIGHT = 941;
  var initialDevicePixelRatio = window.devicePixelRatio || 1;
  var planes = [
    { id: "profileLeftPlane", width: 370, height: 710, target: [[203, 148], [540, 134], [536, 842], [167, 842]] },
    { id: "profileRightPlane", width: 970, height: 710, target: [[540, 134], [1424, 140], [1502, 842], [536, 842]] }
  ];

  function solve(matrix) {
    var rows = matrix.length;
    var cols = matrix[0].length;
    for (var column = 0; column < rows; column += 1) {
      var pivot = column;
      for (var row = column + 1; row < rows; row += 1) {
        if (Math.abs(matrix[row][column]) > Math.abs(matrix[pivot][column])) pivot = row;
      }
      var swap = matrix[column]; matrix[column] = matrix[pivot]; matrix[pivot] = swap;
      var divisor = matrix[column][column];
      if (Math.abs(divisor) < 1e-10) throw new Error("Profile page plane could not be solved.");
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
      var x = from[i][0]; var y = from[i][1]; var u = to[i][0]; var v = to[i][1];
      equations.push([x, y, 1, 0, 0, 0, -x * u, -y * u, u]);
      equations.push([0, 0, 0, x, y, 1, -x * v, -y * v, v]);
    }
    return solve(equations);
  }

  function cssMatrix(values) {
    return "matrix3d(" + [values[0], values[3], 0, values[6], values[1], values[4], 0, values[7], 0, 0, 1, 0, values[2], values[5], 0, 1].join(",") + ")";
  }

  function mapPlanes() {
    planes.forEach(function (plane) {
      var element = document.getElementById(plane.id);
      if (!element) return;
      var source = [[0, 0], [plane.width, 0], [plane.width, plane.height], [0, plane.height]];
      element.style.transform = cssMatrix(homography(source, plane.target));
      element.dataset.quad = plane.target.flat().join(",");
      element.classList.add("is-ready");
    });
  }

  function sizeScene() {
    var scene = document.querySelector(".profile-projected-scene");
    var stage = document.getElementById("profileSceneStage");
    if (!scene || !stage || window.matchMedia("(max-width: 760px)").matches) return;
    var zoomedIn = (window.devicePixelRatio || 1) > initialDevicePixelRatio + 0.01;
    /* At browser zoom-in, keep the physical book at its source size. The
       scrollable scene then provides genuine pan controls rather than silently
       counter-scaling the art back to a fitted, flat-looking canvas. */
    var scale = zoomedIn ? 1 : Math.max(scene.clientWidth / BASE_WIDTH, scene.clientHeight / BASE_HEIGHT);
    document.documentElement.style.setProperty("--profile-scene-scale", scale.toFixed(5));
    stage.style.width = Math.ceil(BASE_WIDTH * scale) + "px";
    stage.style.height = Math.ceil(BASE_HEIGHT * scale) + "px";
    window.requestAnimationFrame(function () {
      scene.scrollLeft = Math.max(0, (scene.scrollWidth - scene.clientWidth) / 2);
      scene.scrollTop = Math.max(0, (scene.scrollHeight - scene.clientHeight) / 2);
    });
  }

  function updatePanMode() {
    var scene = document.querySelector(".profile-projected-scene");
    if (!scene || window.matchMedia("(max-width: 760px)").matches) return;
    var zoomedIn = (window.devicePixelRatio || 1) > initialDevicePixelRatio + 0.01;
    scene.classList.toggle("is-pannable", zoomedIn);
    scene.tabIndex = zoomedIn ? 0 : -1;
  }

  function syncScene() {
    sizeScene();
    updatePanMode();
  }

  window.addEventListener("DOMContentLoaded", function () { mapPlanes(); syncScene(); });
  window.addEventListener("resize", syncScene, { passive: true });
  /* Chromium updates devicePixelRatio on desktop browser zoom. visualViewport
     also catches zoom changes in embedded browsers where window resize is
     delayed, so the fitted and pannable modes cannot get out of sync. */
  if (window.visualViewport) window.visualViewport.addEventListener("resize", syncScene, { passive: true });
})();

(function () {
  var W = 1672, H = 941;
  var initialDpr = window.devicePixelRatio || 1;
  var planes = [
    { id: "storySetupPlane", size: [470, 590], target: [[366, 152], [790, 137], [789, 720], [293, 732]] },
    { id: "storyRecentsPlane", size: [430, 580], target: [[878, 142], [1304, 154], [1378, 731], [878, 720]] }
  ];
  function solve(a) { for (var c = 0; c < 8; c++) { var p = c; for (var r = c + 1; r < 8; r++) if (Math.abs(a[r][c]) > Math.abs(a[p][c])) p = r; var t = a[c]; a[c] = a[p]; a[p] = t; var d = a[c][c]; for (var j = c; j < 9; j++) a[c][j] /= d; for (var i = 0; i < 8; i++) if (i !== c) { var f = a[i][c]; for (var k = c; k < 9; k++) a[i][k] -= f * a[c][k]; } } return a.map(function (r) { return r[8]; }); }
  function matrix(size, target) { var source = [[0,0],[size[0],0],[size[0],size[1]],[0,size[1]]], a = []; source.forEach(function (p, i) { var x=p[0], y=p[1], u=target[i][0], v=target[i][1]; a.push([x,y,1,0,0,0,-x*u,-y*u,u], [0,0,0,x,y,1,-x*v,-y*v,v]); }); var h=solve(a); return "matrix3d(" + [h[0],h[3],0,h[6],h[1],h[4],0,h[7],0,0,1,0,h[2],h[5],0,1].join(",") + ")"; }
  function sizeStage() {
    var stage=document.getElementById("storiesBookStage"), section=document.querySelector(".stories-book-section");
    if (!stage || matchMedia("(max-width: 700px)").matches) return;
    var zoomed=(window.devicePixelRatio || 1) > initialDpr + 0.01;
    section.classList.toggle("is-pannable", zoomed);
    /* Zoom-in retains the original projected book so it can be panned.
       Zoom-out recalculates cover sizing instead of exposing a second,
       independently-scaled backdrop. */
    if (zoomed) return;
    var scale=Math.max(section.clientWidth/W, section.clientHeight/H);
    document.documentElement.style.setProperty("--stories-scale", scale.toFixed(5));
    stage.style.width=Math.ceil(W*scale)+"px";
    stage.style.height=Math.ceil(H*scale)+"px";
    requestAnimationFrame(function () {
      /* Panning leaves an internal scroll offset behind. Clear it when the
         reader returns to its normal, clipped composition. */
      section.scrollLeft=0;
      section.scrollTop=0;
    });
  }
  function setup() { planes.forEach(function (p) { var el=document.getElementById(p.id); el.style.width=p.size[0]+"px"; el.style.height=p.size[1]+"px"; el.style.transform=matrix(p.size,p.target); el.dataset.quad=p.target.flat().join(","); el.classList.add("is-ready"); }); sizeStage(); }
  var levels = [
    ["A1", "Novice", "The sea is calm. The keeper sees a new door."],
    ["A2", "Wayfarer", "The keeper walks the path and notices a door beneath the cliffs."],
    ["B1", "Storyteller", "The sea breathed against the cliffs as the keeper found a door that had never been there before.", true],
    ["B2", "Chronicler", "The wind carried salt and memory while an unexpected door altered the familiar path."],
    ["C1", "Loremaster", "Salt and silence gathered at the cliffs, where the familiar path offered an unfamiliar door."],
    ["C2", "Archivist", "The keeper's long intimacy with the coast was corrected by a door that had no business existing."]
  ];
  function renderBands() { document.getElementById("proficiencyBandList").innerHTML = levels.map(function (level) { return '<article' + (level[3] ? ' class="is-recommended"' : '') + '><span>' + level[0] + '</span><h3>' + level[1] + '</h3><p>' + level[2] + '</p><a href="loading.html">' + (level[3] ? 'Start recommended' : 'Read this version') + ' →</a></article>'; }).join(''); }
  function reveal() { var bands=document.getElementById("proficiencyBands"); renderBands(); bands.hidden=false; bands.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block:"start"}); }
  setup(); window.addEventListener("resize", sizeStage); if (window.visualViewport) window.visualViewport.addEventListener("resize", sizeStage, { passive: true }); document.getElementById("generateBands").addEventListener("click", reveal); document.getElementById("mobileGenerateBands").addEventListener("click", reveal);
})();

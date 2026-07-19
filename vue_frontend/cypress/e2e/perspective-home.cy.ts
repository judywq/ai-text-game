describe('perspective homepage proof', () => {
  it('maps selectable HTML onto the generated left page', () => {
    cy.viewport(1280, 720)
    cy.visit('/mockup-perspective/index.html')
    cy.get('#pagePlane')
      .should('have.class', 'is-ready')
      .and('have.attr', 'data-quad', '265,170,755,110,840,665,275,725')
      .and(($plane) => {
        expect(getComputedStyle($plane[0]).transform).to.match(/^matrix3d/)
        const quad = ($plane.attr('data-quad') ?? '').split(',').map(Number)
        const topSlope = (quad[3] - quad[1]) / (quad[2] - quad[0])
        const bottomSlope = (quad[5] - quad[7]) / (quad[4] - quad[6])
        expect(topSlope).to.be.within(-0.13, -0.11)
        expect(bottomSlope).to.be.within(-0.115, -0.1)
      })
    cy.get('#hero-title').should('be.visible').and('contain.text', 'Every choice')
    cy.get('.primary-nav').should('not.contain.text', 'How it works')
    cy.get('.primary-nav a').contains('About').should('have.attr', 'href', 'about.html')
    cy.get('.sign-in').should('have.attr', 'href', 'login.html')
    cy.get('.scene-plate').should('have.attr', 'alt', '')
    cy.get('.site-footer').should('contain.text', '© 2026 GenQuest')
    cy.get('.footer-links a').eq(0).should('have.attr', 'href', '../mockup/terms.html')
    cy.get('.footer-links a').eq(1).should('have.attr', 'href', '../mockup/privacy.html')
    cy.get('.sign-in').should(($link) => {
      const win = $link[0].ownerDocument.defaultView
      expect($link[0].getBoundingClientRect().right).to.be.at.most(win?.innerWidth ?? 1440)
    })
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(
        (doc.defaultView?.innerWidth ?? doc.documentElement.clientWidth) + 1,
      )
    })
    cy.screenshot('perspective-home-desktop', { capture: 'viewport' })
  })

  it('opens the About placeholder page', () => {
    cy.viewport(1440, 810)
    cy.visit('/mockup-perspective/index.html')
    cy.contains('.primary-nav a', 'About').click()
    cy.location('pathname').should('match', /about\.html$/)
    cy.get('h1').should('contain.text', 'About')
  })

  it('keeps browser zoom from being cancelled and exposes a pannable stage', () => {
    cy.viewport(1440, 810)
    cy.visit('/mockup-perspective/index.html')
    cy.get('.scene').should('not.have.class', 'is-pannable').and('have.css', 'overflow', 'hidden')
    cy.window().then((win) => {
      Object.defineProperty(win, 'devicePixelRatio', {
        configurable: true,
        value: (win.devicePixelRatio || 1) * 1.25,
      })
      win.dispatchEvent(new Event('resize'))
    })
    cy.get('.scene').should('have.class', 'is-pannable').and('have.css', 'overflow', 'auto')
    cy.get('.scene').then(($scene) => {
      const scene = $scene[0] as HTMLElement
      const doc = scene.ownerDocument
      const root = doc.documentElement
      const before = Number.parseFloat(getComputedStyle(root).getPropertyValue('--scene-scale'))
      const beforeStageWidth = (doc.getElementById('sceneStage') as HTMLElement).style.width
      doc.defaultView!.dispatchEvent(new Event('resize'))
      const after = Number.parseFloat(getComputedStyle(root).getPropertyValue('--scene-scale'))
      expect(after).to.equal(before)
      expect((doc.getElementById('sceneStage') as HTMLElement).style.width).to.equal(beforeStageWidth)
      expect(scene.scrollHeight).to.be.greaterThan(scene.clientHeight)
      const start = scene.scrollTop
      scene.scrollTop = start + 80
      expect(scene.scrollTop).to.be.greaterThan(start)
    })
  })

  it('switches to the readable mobile composition', () => {
    cy.viewport(390, 844)
    cy.visit('/mockup-perspective/index.html')
    cy.get('.mobile-hero h1').should('be.visible')
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(
        (doc.defaultView?.innerWidth ?? doc.documentElement.clientWidth) + 1,
      )
    })
    cy.screenshot('perspective-home-mobile', { capture: 'viewport' })
  })
})

describe('perspective login mockup', () => {
  it('maps a live login form onto the clean left page', () => {
    cy.viewport(969, 891)
    cy.visit('/mockup-perspective/login.html')
    cy.get('#loginPlane')
      .should('have.class', 'is-ready')
      .and('have.attr', 'data-quad', '294,124,808,94,825,750,216,780')
      .and(($plane) => {
        expect(getComputedStyle($plane[0]).transform).to.match(/^matrix3d/)
        const quad = ($plane.attr('data-quad') ?? '').split(',').map(Number)
        const topSlope = (quad[3] - quad[1]) / (quad[2] - quad[0])
        const bottomSlope = (quad[5] - quad[7]) / (quad[4] - quad[6])
        expect(topSlope).to.be.within(-0.061, -0.056)
        expect(bottomSlope).to.be.within(-0.051, -0.046)
    })
    cy.get('#login-title').should('be.visible').and('contain.text', 'Login')
    cy.screenshot('perspective-login-desktop', { capture: 'viewport' })
    cy.get('#email').should('be.visible').type('reader@example.com')
    cy.get('#password').should('be.visible').type('storybook')
    cy.get('.password-toggle').click()
    cy.get('#password').should('have.attr', 'type', 'text')
    cy.get('.login-scene-plate').should('have.attr', 'alt', '')
    cy.get('.login-scene-canvas').then(($canvas) => {
      cy.get('.login-scene-plate').then(($plate) => {
        const canvasRect = $canvas[0].getBoundingClientRect()
        const plateRect = $plate[0].getBoundingClientRect()
        expect(Math.abs(canvasRect.width - plateRect.width)).to.be.lessThan(1)
        expect(Math.abs(canvasRect.height - plateRect.height)).to.be.lessThan(1)
      })
    })
  })

  it('provides native panning without counter-scaling browser zoom', () => {
    cy.viewport(969, 891)
    cy.visit('/mockup-perspective/login.html')
    cy.get('.login-scene').should('not.have.class', 'is-pannable').and('have.css', 'overflow', 'hidden')
    cy.window().then((win) => {
      Object.defineProperty(win, 'devicePixelRatio', {
        configurable: true,
        value: (win.devicePixelRatio || 1) * 1.25,
      })
      win.dispatchEvent(new Event('resize'))
    })
    cy.get('.login-scene').should('have.class', 'is-pannable').and('have.css', 'overflow', 'auto')
    cy.get('.login-scene').then(($scene) => {
      const scene = $scene[0] as HTMLElement
      const doc = scene.ownerDocument
      const root = doc.documentElement
      const scale = getComputedStyle(root).getPropertyValue('--scene-scale')
      const stage = doc.getElementById('loginSceneStage') as HTMLElement
      const stageWidth = stage.style.width

      expect(getComputedStyle(scene).overflowX).to.equal('auto')
      expect(scene.scrollWidth).to.be.greaterThan(scene.clientWidth)
      const start = scene.scrollLeft
      scene.scrollLeft = start + 100
      expect(scene.scrollLeft).to.be.greaterThan(start)

      doc.defaultView!.dispatchEvent(new Event('resize'))
      expect(getComputedStyle(root).getPropertyValue('--scene-scale')).to.equal(scale)
      expect(stage.style.width).to.equal(stageWidth)
    })
  })

  it('keeps the legal footer in the same place on every perspective page', () => {
    cy.viewport(1440, 810)
    ;['index.html', 'about.html', 'login.html'].forEach((page) => {
      cy.visit(`/mockup-perspective/${page}`)
      cy.get('.site-footer').should(($footer) => {
        const rect = $footer[0].getBoundingClientRect()
        const win = $footer[0].ownerDocument.defaultView!
        expect(Math.abs(rect.bottom - win.innerHeight)).to.be.lessThan(1.1)
      })
      cy.get('.footer-links a').then(($links) => {
        expect($links.eq(0)).to.contain('Terms of Service')
        expect($links.eq(1)).to.contain('Privacy Policy')
      })
    })
  })

  it('uses the readable mobile form composition', () => {
    cy.viewport(390, 844)
    cy.visit('/mockup-perspective/login.html')
    cy.get('.login-mobile-card h1').should('be.visible').and('contain.text', 'Login')
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(
        (doc.defaultView?.innerWidth ?? doc.documentElement.clientWidth) + 1,
      )
    })
    cy.screenshot('perspective-login-mobile', { capture: 'viewport' })
  })
})

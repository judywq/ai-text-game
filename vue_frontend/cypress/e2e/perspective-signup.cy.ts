describe('signup page', () => {
  // Calibrated writing plane on the blank right page, clockwise from top-left,
  // in canvas coordinates (the 1672x941 artwork clipped to its 808px book
  // region). Kept in sync with signup-perspective.js.
  const QUAD = '870,49,1354,75,1421,732,891,727'
  const PLANE_W = 448
  const PLANE_H = 590

  // Project a plane-local point through the rendered matrix3d, applying the
  // perspective divide, to recover its position in scene-image coordinates.
  const projectCorner = (plane: Element, x: number, y: number) => {
    const m = new DOMMatrix(getComputedStyle(plane).transform)
    const p = m.transformPoint(new DOMPoint(x, y, 0, 1))
    return { x: p.x / p.w, y: p.y / p.w }
  }

  it('keeps live controls on the reconstructed reader-passport book', () => {
    cy.viewport(1280, 720)
    cy.visit('/mockup-perspective/signup.html')

    cy.get('.gq-signup__reference').should('have.attr', 'src', 'assets/signup-page.png')
    cy.get('.gq-signup__header').should('contain.text', 'Back to home')

    cy.get('#signupPlane')
      .should('have.class', 'is-ready')
      .and('have.attr', 'data-quad', QUAD)
      .and(($plane) => {
        expect(getComputedStyle($plane[0]).transform).to.match(/^matrix3d/)
      })

    // Perspective requirement: the projected plane corners must land on the
    // calibrated quad, so every control edge runs parallel to the visible
    // writing-frame tangents rather than sitting axis-aligned.
    cy.get('#signupPlane').should(($plane) => {
      const plane = $plane[0]
      const want = QUAD.split(',').map(Number)
      const corners = [
        projectCorner(plane, 0, 0),
        projectCorner(plane, PLANE_W, 0),
        projectCorner(plane, PLANE_W, PLANE_H),
        projectCorner(plane, 0, PLANE_H),
      ]
      corners.forEach((c, i) => {
        expect(c.x, `corner ${i} x`).to.be.closeTo(want[i * 2], 1.5)
        expect(c.y, `corner ${i} y`).to.be.closeTo(want[i * 2 + 1], 1.5)
      })
      const topSlope = (corners[1].y - corners[0].y) / (corners[1].x - corners[0].x)
      const bottomSlope = (corners[2].y - corners[3].y) / (corners[2].x - corners[3].x)
      // Measured on the artwork: the frame's top rule descends toward the
      // outer edge (~+0.054) while the bottom is nearly level (~+0.008).
      // Guard the sign, because an inverted tilt still "looks projected" while
      // running against the page, which is the failure this page regressed on.
      expect(topSlope, 'top edge descends toward the outer edge').to.be.greaterThan(0.03)
      expect(bottomSlope, 'bottom edge is near level').to.be.within(0, 0.03)
      expect(topSlope, 'edges converge toward the vanishing point')
        .to.be.greaterThan(bottomSlope + 0.02)
    })

    cy.screenshot('signup-clean', { capture: 'viewport' })

    cy.get('#signupName').type('Judy Reader')
    cy.get('#signupEmail').type('reader@example.com')
    cy.get('#signupPassword').type('storybook')
    cy.get('#signupConfirm').type('storybook')

    cy.get('[aria-controls="signupPassword"]').click()
    cy.get('#signupPassword').should('have.attr', 'type', 'text')
    // Revealing one password must not reveal the other.
    cy.get('#signupConfirm').should('have.attr', 'type', 'password')
    cy.get('[aria-controls="signupConfirm"]').click()
    cy.get('#signupConfirm').should('have.attr', 'type', 'text')

    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.be.at.most(document.documentElement.clientWidth + 1)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
    cy.screenshot('signup-fresh', { capture: 'viewport' })
  })

  it('falls back to a readable single-plane card on mobile', () => {
    cy.viewport(375, 812)
    cy.visit('/mockup-perspective/signup.html')
    cy.get('#signupSceneStage').should('not.be.visible')
    cy.get('.signup-mobile-card').should('be.visible')
    cy.get('.signup-mobile-card .login-field').should('have.length', 4)
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.be.at.most(document.documentElement.clientWidth + 1)
    })
  })
})

describe('profile mockup', () => {
  it('projects the live profile controls onto the supplied book pages', () => {
    cy.viewport(1280, 720)
    cy.visit('/mockup-perspective/profile.html')
    cy.clearLocalStorage()
    cy.reload()
    cy.contains('Judy’s Library').should('be.visible')
    cy.get('#profile-heading').should('have.text', 'Profile')
    cy.get('.profile-project-account').should('contain.text', 'Profile')
    cy.get('#profileSaved').should('not.be.visible')
    cy.get('#languageMenu').should('be.visible')
    cy.get('#explanationLanguage').should('have.value', 'French')
    cy.screenshot('profile-initial', { capture: 'viewport' })
    cy.get('[data-language="Japanese"]').click()
    cy.get('#explanationLanguage').should('have.value', 'Japanese')
    cy.get('#languageMenu').should('not.be.visible')
    cy.get('.profile-save').click()
    cy.get('#profileSaved').should('be.visible').and('contain.text', 'updated')
    cy.get('#profileLeftPlane').should(($plane) => {
      expect(getComputedStyle($plane[0]).transform).to.contain('matrix3d')
    })
    cy.get('#profileRightPlane').should(($plane) => {
      expect(getComputedStyle($plane[0]).transform).to.contain('matrix3d')
    })
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.be.at.most(document.documentElement.clientWidth + 1)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
    cy.window().then((win) => {
      Object.defineProperty(win, 'devicePixelRatio', {
        configurable: true,
        value: (win.devicePixelRatio || 1) + 0.5,
      })
      win.dispatchEvent(new Event('resize'))
    })
    cy.get('.profile-projected-scene').should('have.class', 'is-pannable')
    cy.get('.profile-projected-scene').should(($scene) => {
      expect($scene[0].scrollWidth).to.be.greaterThan($scene[0].clientWidth)
      expect($scene[0].scrollHeight).to.be.greaterThan($scene[0].clientHeight)
    })
    cy.get('#profileSceneStage').should(($stage) => {
      expect(parseFloat(getComputedStyle($stage[0]).width)).to.eq(1672)
    })
    cy.window().then((win) => {
      delete (win as Window & { devicePixelRatio?: number }).devicePixelRatio
      win.dispatchEvent(new Event('resize'))
    })
    cy.get('.profile-projected-scene').should('not.have.class', 'is-pannable')
    cy.get('.profile-projected-header').should('be.visible')
    cy.screenshot('profile-book', { capture: 'viewport' })
  })
})

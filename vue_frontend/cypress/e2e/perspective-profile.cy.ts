describe('profile mockup', () => {
  it('keeps reader settings in a stable book spread', () => {
    cy.viewport(1280, 720)
    cy.visit('/mockup-perspective/profile.html')
    cy.contains('Judy’s Library').should('be.visible')
    cy.get('#profile-heading').should('have.text', 'Profile')
    cy.get('.profile-account').should('contain.text', 'Profile')
    cy.get('#profileSaved').should('not.be.visible')
    cy.get('#languageMenu').should('be.visible')
    cy.get('#explanationLanguage').should('have.value', 'French')
    cy.get('[data-language="Japanese"]').click()
    cy.get('#explanationLanguage').should('have.value', 'Japanese')
    cy.get('.profile-save').click()
    cy.get('#profileSaved').should('be.visible').and('contain.text', 'updated')
    cy.get('.profile-book').should(($book) => {
      expect(getComputedStyle($book[0]).transform).to.contain('matrix3d')
    })
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.be.at.most(document.documentElement.clientWidth + 1)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
    cy.get('.profile-book').then(($book) => cy.get('.site-footer').then(($footer) => {
      expect($book[0].getBoundingClientRect().bottom).to.be.at.most($footer[0].getBoundingClientRect().top + 1)
    }))
    cy.screenshot('profile-book', { capture: 'viewport' })
  })
})

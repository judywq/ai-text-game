describe('perspective loading mockup', () => {
  it('uses the original game guide content and unlocks the start action', () => {
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/loading.html')
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.equal(doc.documentElement.clientWidth)
    })
    cy.get('.loading-book-panel').should('be.visible')
    cy.get('.tutorial-card.is-active img').should('have.attr', 'src').and('include', 'assets/gameplay-slide.png')
    cy.get('.tutorial-card.is-active img').should(($image) => {
      expect($image[0].naturalWidth).to.be.greaterThan(0)
    })
    cy.contains('If you are having trouble understanding any words or phrases in the story').should('be.visible')
    cy.get('#loadingDots button').eq(1).click()
    cy.contains('Everything you look up is kept in the notebook beside the story').should('be.visible')
    cy.get('#loadingStart').should('have.attr', 'aria-disabled', 'false')
    cy.screenshot('perspective-loading-book', { capture: 'viewport' })
  })
})

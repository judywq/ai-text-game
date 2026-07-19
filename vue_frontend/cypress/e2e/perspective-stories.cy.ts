describe('perspective stories mockup', () => {
  it('uses projected setup pages before revealing flat proficiency bands', () => {
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/stories.html')
    cy.get('#storySetupPlane').should('have.class', 'is-ready').and('have.attr', 'data-quad', '366,152,790,137,789,720,293,732')
    cy.get('#storyRecentsPlane').should('have.class', 'is-ready').and('have.attr', 'data-quad', '878,142,1304,154,1378,731,878,720')
    cy.get('#storySetupPlane select').should('be.visible')
    cy.get('#recent-stories-title').should('be.visible')
    cy.get('#proficiencyBands').should('have.attr', 'hidden')
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.equal(document.documentElement.clientWidth)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
    cy.screenshot('perspective-stories-book', { capture: 'viewport' })
    cy.get('#generateBands').click()
    cy.get('#proficiencyBands').should('not.have.attr', 'hidden')
    cy.get('#proficiencyBands').within(() => {
      cy.contains('Choose your proficiency band').should('be.visible')
      cy.contains('B1').should('be.visible')
      cy.contains('C2').should('be.visible')
      cy.get('.proficiency-bands article').should('have.length', 6)
      cy.get('.proficiency-bands').should('have.css', 'grid-template-columns').then((value) => {
        expect(value.trim().split(/\s+/)).to.have.length(3)
      })
    })
  })

  it('clears panning and returns to one clipped book after browser zoom is reset', () => {
    let initialDpr = 1
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/stories.html')
    cy.window().then((window) => {
      initialDpr = window.devicePixelRatio
      Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: initialDpr + 0.25 })
      window.dispatchEvent(new window.Event('resize'))
      window.visualViewport?.dispatchEvent(new window.Event('resize'))
    })
    cy.get('.stories-book-section').should('have.class', 'is-pannable').then(($section) => {
      $section[0].scrollLeft = 80
      $section[0].scrollTop = 80
    })
    cy.window().then((window) => {
      Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: initialDpr })
      window.dispatchEvent(new window.Event('resize'))
      window.visualViewport?.dispatchEvent(new window.Event('resize'))
    })
    cy.get('.stories-book-section').should('not.have.class', 'is-pannable').should(($section) => {
      expect($section[0].scrollLeft).to.equal(0)
      expect($section[0].scrollTop).to.equal(0)
    })
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.equal(document.documentElement.clientWidth)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
  })
})

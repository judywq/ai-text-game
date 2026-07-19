describe('perspective library mockup', () => {
  it('keeps both live content planes clear of the book gutter', () => {
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/library.html')
    cy.get('#libraryListPlane').should('have.class', 'is-ready').and('have.attr', 'data-quad', '366,152,773,138,770,719,294,732')
    cy.get('#libraryDetailPlane').should('have.class', 'is-ready').and('have.attr', 'data-quad', '900,143,1303,154,1377,730,901,720')
    cy.get('#libraryListPlane').then(($left) => cy.get('#libraryDetailPlane').then(($right) => {
      const left = ($left.attr('data-quad') ?? '').split(',').map(Number)
      const right = ($right.attr('data-quad') ?? '').split(',').map(Number)
      expect(Math.max(left[2], left[4])).to.be.lessThan(800)
      expect(Math.min(right[0], right[6])).to.be.greaterThan(870)
    }))
    cy.contains('The Bell in the Mist').should('be.visible')
    cy.contains('Resume chapter 4').should('be.visible')
    cy.get('#library-filter').select('Completed').should('have.value', 'Completed')
    cy.contains('Unique words encountered').should('be.visible')
    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.equal(document.documentElement.clientWidth)
      expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
    })
    cy.screenshot('perspective-library-book', { capture: 'viewport' })
  })

  it('keeps the book pannable instead of rescaling it during browser zoom', () => {
    let initialDpr = 1
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/library.html')
    cy.get('#libraryBookStage').then(($stage) => {
      const initialWidth = $stage[0].getBoundingClientRect().width
      cy.window().then((window) => {
        initialDpr = window.devicePixelRatio
        Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: initialDpr + 0.25 })
      })
      cy.viewport(1100, 700)
      cy.get('.library-book-section').should('have.class', 'is-pannable')
      cy.get('#libraryBookStage').then(($zoomedStage) => {
        expect($zoomedStage[0].getBoundingClientRect().width).to.equal(initialWidth)
      })
      cy.get('.library-book-section').then(($section) => {
        expect($section[0].scrollWidth).to.be.greaterThan($section[0].clientWidth)
        $section[0].scrollLeft = 80
        $section[0].scrollTop = 80
      })
      cy.window().then((window) => {
        Object.defineProperty(window, 'devicePixelRatio', { configurable: true, value: initialDpr })
        window.dispatchEvent(new window.Event('resize'))
        window.visualViewport?.dispatchEvent(new window.Event('resize'))
      })
      cy.get('.library-book-section').should('not.have.class', 'is-pannable').should(($section) => {
        expect($section[0].scrollLeft).to.equal(0)
        expect($section[0].scrollTop).to.equal(0)
      })
      cy.document().then((document) => {
        expect(document.documentElement.scrollWidth).to.equal(document.documentElement.clientWidth)
        expect(document.documentElement.scrollHeight).to.be.at.most(document.documentElement.clientHeight + 1)
      })
    })
  })
})

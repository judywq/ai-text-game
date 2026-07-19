describe('vocabulary review mockup', () => {
  it('keeps the review spread usable and scores submitted answers', () => {
    cy.visit('/mockup-perspective/quiz.html', { onBeforeLoad(win) { win.localStorage.removeItem('gq-notes-v1') } })
    cy.get('.review-book').should('be.visible')
    cy.get('.review-book').then(($book) => {
      const book = $book[0].getBoundingClientRect()
      const center = book.left + book.width / 2
      cy.get('#reviewPrev').then(($prev) => expect($prev[0].getBoundingClientRect().right).to.be.lessThan(center))
      cy.get('#reviewNext').then(($next) => expect($next[0].getBoundingClientRect().left).to.be.greaterThan(center))
      cy.get('#reviewLeftPageNumber').then(($page) => expect($page[0].getBoundingClientRect().right).to.be.lessThan(center))
      cy.get('#reviewRightPageNumber').then(($page) => expect($page[0].getBoundingClientRect().left).to.be.greaterThan(center))
    })
    cy.get('.review-book').then(($book) => {
      const fold = getComputedStyle($book[0], '::after')
      expect(fold.bottom).to.equal('0px')
      expect(fold.backgroundImage).to.contain('linear-gradient')
    })
    cy.get('.review-term').should('have.length', 3)
    cy.get('.review-term textarea').should('have.length', 3)
    cy.get('.review-term textarea').then(($fields) => cy.get('.review-pages').then(($pager) => {
      const pagerTop = $pager[0].getBoundingClientRect().top
      Array.from($fields).forEach((field) => {
        expect((field as HTMLTextAreaElement).getBoundingClientRect().bottom).to.be.lessThan(pagerTop)
      })
    }))
    cy.get('.review-term').then(($terms) => {
      const gaps = Array.from($terms).map((term) => {
        const context = term.querySelector('.review-context') as HTMLElement
        const label = term.querySelector('label') as HTMLElement
        return label.getBoundingClientRect().top - context.getBoundingClientRect().bottom
      })
      expect(Math.max(...gaps) - Math.min(...gaps)).to.be.at.most(1)
    })
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(doc.documentElement.clientWidth + 1)
      expect(doc.documentElement.scrollHeight).to.be.at.most(doc.documentElement.clientHeight + 1)
    })
    cy.get('.review-term textarea').each(($field) => expect($field[0].getBoundingClientRect().bottom).to.be.at.most(Cypress.config('viewportHeight') - 42))
    cy.get('.review-book').then(($book) => cy.get('.site-footer').then(($footer) => {
      expect($book[0].getBoundingClientRect().bottom).to.be.at.most($footer[0].getBoundingClientRect().top + 1)
    }))
    cy.screenshot('vocabulary-review-default', { capture: 'viewport' })
    cy.get('[data-answer="0"]').type('To move closer from every side')
    cy.get('[data-answer="1"]').type('To curl around in a winding shape')
    cy.get('[data-answer="2"]').type('To ring slowly with a deep sound')
    cy.get('#reviewSubmit').click()
    cy.get('#reviewResults').should('be.visible')
    cy.get('#reviewScore').should('contain.text', '1.00')
    cy.get('.review-result-row').should('have.length', 3)
    cy.screenshot('vocabulary-review-results', { capture: 'viewport' })
  })

  it('paginates a long phrase list without losing answers', () => {
    const notes = Array.from({ length: 7 }, (_, index) => ({
      id: String(index + 1),
      storyId: 104,
      phrase: `phrase ${index + 1}`,
      context: `This is the story context for queried phrase ${index + 1}.`,
    }))
    cy.visit('/mockup-perspective/quiz.html', {
      onBeforeLoad(win) { win.localStorage.setItem('gq-notes-v1', JSON.stringify(notes)) },
    })

    cy.get('#reviewLeftPageNumber').should('have.text', '1')
    cy.get('#reviewRightPageNumber').should('have.text', '2')
    cy.get('#reviewPageStatus').should('contain.text', 'Spread 1 of 3')
    cy.get('.review-term').should('have.length', 3)
    cy.get('#reviewPrev').should('be.disabled')
    cy.get('#reviewSubmitRow').should('not.be.visible')
    cy.get('.review-term textarea').each(($field) => cy.wrap($field).type('A clear four word explanation'))

    cy.get('#reviewNext').click()
    cy.get('#reviewLeftPageNumber').should('have.text', '3')
    cy.get('#reviewRightPageNumber').should('have.text', '4')
    cy.get('.review-term').should('have.length', 3)
    cy.get('.review-term textarea').each(($field) => cy.wrap($field).type('A clear four word explanation'))

    cy.get('#reviewNext').click()
    cy.get('#reviewLeftPageNumber').should('have.text', '5')
    cy.get('#reviewRightPageNumber').should('have.text', '6')
    cy.get('.review-term').should('have.length', 1)
    cy.get('#reviewNext').should('be.disabled')
    cy.get('#reviewSubmitRow').should('be.visible')
    cy.get('.review-term textarea').type('A clear four word explanation')

    cy.get('#reviewPrev').click().click()
    cy.get('#reviewLeftPageNumber').should('have.text', '1')
    cy.get('#reviewRightPageNumber').should('have.text', '2')
    cy.get('[data-answer="0"]').should('have.value', 'A clear four word explanation')
    cy.get('#reviewNext').click().click()
    cy.get('#reviewSubmit').click()
    cy.get('#reviewScore').should('contain.text', '1.00')
    cy.get('.review-result-row').should('have.length', 1)
    cy.get('#reviewPrev').click()
    cy.get('.review-result-row').should('have.length', 3)
    cy.screenshot('vocabulary-review-paginated', { capture: 'viewport' })
  })

  it('keeps form fields out of the folio strip in a short zoomed viewport', () => {
    cy.viewport(1280, 520)
    cy.visit('/mockup-perspective/quiz.html', { onBeforeLoad(win) { win.localStorage.removeItem('gq-notes-v1') } })
    cy.get('.review-term textarea').then(($fields) => cy.get('.review-pages').then(($pager) => {
      const pagerTop = $pager[0].getBoundingClientRect().top
      Array.from($fields).forEach((field) => {
        expect((field as HTMLTextAreaElement).getBoundingClientRect().bottom).to.be.lessThan(pagerTop)
      })
    }))
    cy.screenshot('vocabulary-review-short-viewport', { capture: 'viewport' })
  })
})

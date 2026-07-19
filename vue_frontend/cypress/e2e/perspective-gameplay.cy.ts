describe('gameplay reader interactions', () => {
  it('paginates with a page turn and supports vocabulary queries', () => {
    cy.viewport(1440, 900)
    cy.visit('/mockup-perspective/gameplay.html')
    cy.document().then((doc) => {
      expect(doc.documentElement.scrollWidth).to.be.at.most(doc.documentElement.clientWidth + 1)
    })
    cy.get('.gameplay-notes').should('have.attr', 'data-open', 'true')
    cy.get('.gameplay-notes').then(($notes) => cy.get('.site-footer').then(($footer) => {
      expect($notes[0].getBoundingClientRect().bottom).to.be.at.most($footer[0].getBoundingClientRect().top + 1)
    }))
    cy.get('[data-story-page="1"] .story-page-copy > :last-child').then(($content) => cy.get('.gameplay-pages').then(($pages) => {
      expect($content[0].getBoundingClientRect().bottom).to.be.at.most($pages[0].getBoundingClientRect().top + 1)
    }))
    cy.get('[data-story-page="1"] .story-page-copy').then(($copy) => cy.get('.gameplay-pages').then(($pages) => {
      const gap = $pages[0].getBoundingClientRect().top - $copy[0].getBoundingClientRect().bottom
      expect(gap).to.be.closeTo(12, 2)
    }))
    cy.get('.gameplay-story-content').should('have.css', 'overflow-y', 'visible')
    cy.get('.story-next').click()
    cy.get('.gameplay-story-content').should('have.class', 'is-turning')
    cy.get('[data-story-page="1"]').then(($page) => {
      const animation = $page[0].getAnimations()[0]
      expect(animation).to.exist
      animation.pause()
      animation.currentTime = 130
    })
    cy.screenshot('gameplay-whole-page-turn', { capture: 'viewport' })
    cy.get('[data-story-page="1"]').then(($page) => $page[0].getAnimations()[0]?.play())
    cy.get('.story-page-number').should('have.text', '2')
    cy.get('[data-story-page="2"]').should('not.have.attr', 'hidden')
    cy.get('[data-story-page="2"] h1, [data-story-page="2"] .story-plane-kicker').should('not.exist')
    cy.get('[data-story-page="2"] .gameplay-choices').then(($content) => cy.get('.gameplay-pages').then(($pages) => {
      expect($content[0].getBoundingClientRect().bottom).to.be.at.most($pages[0].getBoundingClientRect().top + 1)
    }))
    cy.screenshot('gameplay-page-two', { capture: 'viewport' })
    cy.get('.story-prev').click()
    cy.get('.story-page-number').should('have.text', '1')

    cy.get('[data-story-page="1"] .story-page-copy > p:not(.story-plane-kicker)').first().then(($paragraph) => {
      const text = $paragraph[0].firstChild as Text
      const phrase = 'Mist coils'
      const start = text.data.indexOf(phrase)
      const range = $paragraph[0].ownerDocument.createRange()
      range.setStart(text, start)
      range.setEnd(text, start + phrase.length)
      const selection = $paragraph[0].ownerDocument.defaultView!.getSelection()!
      selection.removeAllRanges()
      selection.addRange(range)
      $paragraph[0].dispatchEvent(new MouseEvent('mouseup', { bubbles: true }))
    })
    cy.get('.lookup-btn').should('be.visible').click()
    cy.get('.query-dialog').should('have.attr', 'open')
    cy.get('#queryPhrase').should('have.text', 'Mist coils')
    cy.get('.notes-count').should('have.text', '1')
    cy.screenshot('gameplay-query-open', { capture: 'viewport' })
    cy.get('.query-close').click()
    cy.get('mark.lookup').should('have.text', 'Mist coils')
    cy.screenshot('gameplay-notebook-boundary', { capture: 'viewport' })
  })
})

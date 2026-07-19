describe('GenQuest image-led prototype', () => {
  beforeEach(() => {
    cy.viewport(1280, 720)
    cy.visit('/mockup/home')
  })

  it('renders the approved artwork and exposes all prototype screens', () => {
    cy.get('.screen-image')
      .should('be.visible')
      .and(($image) => {
        const element = $image[0] as HTMLImageElement
        expect(element.naturalWidth).to.equal(1672)
        expect(element.naturalHeight).to.equal(941)
      })

    cy.document().then((document) => {
      expect(document.documentElement.scrollWidth).to.be.at.most(
        document.documentElement.clientWidth,
      )
      expect(document.documentElement.scrollHeight).to.be.at.most(
        document.documentElement.clientHeight,
      )
    })

    cy.screenshot('mockup-home-laptop', { capture: 'viewport' })

    cy.contains('button', 'Screens').click()
    cy.get('#prototype-screen-menu').should('be.visible')
    cy.get('#prototype-screen-menu .drawer-group button').should('have.length', 17)

    cy.contains('#prototype-screen-menu button', 'Vocabulary review').click()
    cy.url().should('include', '/mockup/vocabulary-review')
    cy.get('.route-plaque').should('contain.text', '/game/:id/quiz')

    cy.contains('button', 'Screens').click()
    cy.contains('#prototype-screen-menu button', 'Show clickable areas').click()
    cy.get('.prototype-shell').should('have.class', 'show-hotspots')
    cy.get('.screen-hotspot').its('length').should('be.greaterThan', 0)
  })

  it('supports keyboard paging and a narrow viewport', () => {
    cy.get('body').trigger('keydown', { key: 'ArrowRight' })
    cy.url().should('include', '/mockup/login')

    cy.viewport(390, 844)
    cy.visit('/mockup/vocabulary-review')
    cy.get('.screen-image').should('be.visible')
    cy.get('.menu-trigger').should('be.visible')
    cy.get('.prototype-pager').should('be.visible')
  })
})

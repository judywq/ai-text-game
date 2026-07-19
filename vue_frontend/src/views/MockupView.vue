<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import changePasswordImage from '@/assets/ui-concepts/pages/change-password.png'
import forgotPasswordImage from '@/assets/ui-concepts/pages/forgot-password.png'
import gameLoadingImage from '@/assets/ui-concepts/pages/game-loading.png'
import gameplayImage from '@/assets/ui-concepts/pages/gameplay.png'
import gameScenarioImage from '@/assets/ui-concepts/pages/game-scenario.png'
import historyImage from '@/assets/ui-concepts/pages/history.png'
import homeImage from '@/assets/ui-concepts/pages/home.png'
import loginImage from '@/assets/ui-concepts/pages/login.png'
import notFoundImage from '@/assets/ui-concepts/pages/not-found.png'
import passwordResetSentImage from '@/assets/ui-concepts/pages/password-reset-sent.png'
import privacyImage from '@/assets/ui-concepts/pages/privacy.png'
import profileImage from '@/assets/ui-concepts/pages/profile.png'
import resetPasswordImage from '@/assets/ui-concepts/pages/reset-password.png'
import signupImage from '@/assets/ui-concepts/pages/signup.png'
import termsImage from '@/assets/ui-concepts/pages/terms.png'
import verifyEmailImage from '@/assets/ui-concepts/pages/verify-email.png'
import vocabularyReviewImage from '@/assets/ui-concepts/pages/vocabulary-review.png'

type ScreenId =
  | 'home'
  | 'login'
  | 'signup'
  | 'verify-email'
  | 'forgot-password'
  | 'password-reset-sent'
  | 'reset-password'
  | 'game-scenario'
  | 'game-loading'
  | 'gameplay'
  | 'vocabulary-review'
  | 'history'
  | 'profile'
  | 'change-password'
  | 'terms'
  | 'privacy'
  | 'not-found'

interface Hotspot {
  label: string
  target: ScreenId
  x: number
  y: number
  width: number
  height: number
}

interface PrototypeScreen {
  id: ScreenId
  label: string
  route: string
  group: 'Discover' | 'Account' | 'Story' | 'Library' | 'Reference'
  image: string
  description: string
  hotspots: Hotspot[]
}

const globalNavHotspots: Hotspot[] = [
  { label: 'Open stories', target: 'game-scenario', x: 37, y: 1.5, width: 8.5, height: 7 },
  { label: 'Open library', target: 'history', x: 54, y: 1.5, width: 10, height: 7 },
]

const screens: PrototypeScreen[] = [
  {
    id: 'home',
    label: 'Homepage',
    route: '/',
    group: 'Discover',
    image: homeImage,
    description: 'GenQuest homepage with the primary story invitation and illustrated open book.',
    hotspots: [
      { label: 'Begin a story', target: 'game-scenario', x: 7, y: 47, width: 20, height: 11 },
      { label: 'Explore stories', target: 'game-scenario', x: 7, y: 59, width: 15, height: 8 },
      { label: 'Sign in', target: 'login', x: 85, y: 2, width: 10, height: 8 },
      { label: 'Open library', target: 'history', x: 55, y: 2, width: 10, height: 7 },
    ],
  },
  {
    id: 'login',
    label: 'Login',
    route: '/auth/login',
    group: 'Account',
    image: loginImage,
    description: 'Login form presented as the left page of a welcoming library book.',
    hotspots: [
      { label: 'Back to home', target: 'home', x: 20, y: 1.5, width: 12, height: 7 },
      { label: 'Forgot password', target: 'forgot-password', x: 35, y: 50, width: 10, height: 6 },
      { label: 'Log in', target: 'game-scenario', x: 20, y: 60, width: 24, height: 8 },
      { label: 'Create account', target: 'signup', x: 34, y: 70, width: 8, height: 6 },
      { label: 'Terms of service', target: 'terms', x: 44, y: 94, width: 10, height: 5 },
      { label: 'Privacy policy', target: 'privacy', x: 55, y: 94, width: 9, height: 5 },
    ],
  },
  {
    id: 'signup',
    label: 'Create account',
    route: '/auth/signup',
    group: 'Account',
    image: signupImage,
    description: 'Reader passport and account creation form.',
    hotspots: [
      { label: 'Back to home', target: 'home', x: 13, y: 1, width: 12, height: 7 },
      { label: 'Sign up', target: 'verify-email', x: 56, y: 71, width: 25, height: 8 },
      { label: 'Log in instead', target: 'login', x: 72, y: 78, width: 7, height: 6 },
    ],
  },
  {
    id: 'verify-email',
    label: 'Verify email',
    route: '/auth/verify-email',
    group: 'Account',
    image: verifyEmailImage,
    description: 'Six-cell email verification letter with a sealed envelope.',
    hotspots: [
      { label: 'Back to login', target: 'login', x: 87, y: 1, width: 10, height: 7 },
      { label: 'Verify email', target: 'game-scenario', x: 27, y: 59, width: 20, height: 8 },
      { label: 'Back to login', target: 'login', x: 33, y: 67, width: 10, height: 6 },
    ],
  },
  {
    id: 'forgot-password',
    label: 'Forgot password',
    route: '/auth/forgot-password',
    group: 'Account',
    image: forgotPasswordImage,
    description: 'Password recovery letter with a single email field.',
    hotspots: [
      { label: 'Back to login', target: 'login', x: 88, y: 1, width: 10, height: 7 },
      { label: 'Send reset link', target: 'password-reset-sent', x: 22, y: 55, width: 25, height: 10 },
      { label: 'Back to login', target: 'login', x: 36, y: 65, width: 9, height: 6 },
    ],
  },
  {
    id: 'password-reset-sent',
    label: 'Reset email sent',
    route: '/auth/password-reset-sent',
    group: 'Account',
    image: passwordResetSentImage,
    description: 'Confirmation letter showing that a password reset email was sent.',
    hotspots: [
      { label: 'Back to login', target: 'login', x: 34, y: 62, width: 18, height: 8 },
      { label: 'Send another email', target: 'forgot-password', x: 37, y: 70, width: 14, height: 6 },
    ],
  },
  {
    id: 'reset-password',
    label: 'Reset password',
    route: '/auth/reset-password/:uid/:token',
    group: 'Account',
    image: resetPasswordImage,
    description: 'Password reset form paired with an illustrated antique key.',
    hotspots: [
      { label: 'Back to login', target: 'login', x: 88, y: 1, width: 10, height: 7 },
      { label: 'Reset password', target: 'login', x: 56, y: 65, width: 26, height: 9 },
    ],
  },
  {
    id: 'game-scenario',
    label: 'Start adventure',
    route: '/game',
    group: 'Story',
    image: gameScenarioImage,
    description: 'Story workshop for choosing a genre, scene details, and reading level.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Generate scenes', target: 'game-scenario', x: 15, y: 67, width: 15, height: 9 },
      { label: 'Continue recent story', target: 'gameplay', x: 51, y: 21, width: 31, height: 8 },
      { label: 'View all history', target: 'history', x: 50, y: 43, width: 10, height: 6 },
      { label: 'Start at selected level', target: 'game-loading', x: 57, y: 77, width: 15, height: 8 },
      { label: 'Open profile', target: 'profile', x: 82, y: 1, width: 9, height: 8 },
    ],
  },
  {
    id: 'game-loading',
    label: 'Story loading',
    route: '/game/:id/loading',
    group: 'Story',
    image: gameLoadingImage,
    description: 'Immersive rotating story tip while the first chapter is initialized.',
    hotspots: [
      { label: 'Start game', target: 'gameplay', x: 67, y: 84, width: 9, height: 15 },
      { label: 'Continue when ready', target: 'gameplay', x: 37, y: 64, width: 30, height: 14 },
    ],
  },
  {
    id: 'gameplay',
    label: 'Story gameplay',
    route: '/game/:id',
    group: 'Story',
    image: gameplayImage,
    description: 'Interactive chapter spread with story choices and page-turn navigation.',
    hotspots: [
      { label: 'Choose follow the sound', target: 'gameplay', x: 56, y: 56, width: 28, height: 7 },
      { label: 'Choose search the woods', target: 'gameplay', x: 56, y: 64, width: 28, height: 7 },
      { label: 'Choose turn back', target: 'gameplay', x: 56, y: 71, width: 28, height: 7 },
      { label: 'Open vocabulary review', target: 'vocabulary-review', x: 77, y: 79, width: 8, height: 8 },
      { label: 'Previous page', target: 'game-scenario', x: 13, y: 78, width: 8, height: 8 },
    ],
  },
  {
    id: 'vocabulary-review',
    label: 'Vocabulary review',
    route: '/game/:id/quiz',
    group: 'Story',
    image: vocabularyReviewImage,
    description: 'Free-text vocabulary review with contextual scoring and feedback.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Back to story', target: 'gameplay', x: 69, y: 11, width: 10, height: 7 },
      { label: 'Submit answers', target: 'vocabulary-review', x: 61, y: 50, width: 11, height: 7 },
      { label: 'Open profile', target: 'profile', x: 80, y: 0.5, width: 11, height: 7 },
    ],
  },
  {
    id: 'history',
    label: 'Game history',
    route: '/history',
    group: 'Library',
    image: historyImage,
    description: 'Personal library ledger listing stories, genres, statuses, and dates.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Start a new game', target: 'game-scenario', x: 72, y: 17, width: 13, height: 8 },
      { label: 'Continue The Bell in the Mist', target: 'gameplay', x: 15, y: 39, width: 71, height: 8 },
      { label: 'Open profile', target: 'profile', x: 82, y: 1, width: 9, height: 8 },
    ],
  },
  {
    id: 'profile',
    label: 'Profile',
    route: '/profile',
    group: 'Account',
    image: profileImage,
    description: 'Reader settings page for choosing the explanation language.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Change password', target: 'change-password', x: 13, y: 58, width: 18, height: 8 },
      { label: 'Save profile', target: 'profile', x: 34, y: 70, width: 16, height: 10 },
      { label: 'Sign out', target: 'home', x: 14, y: 67, width: 12, height: 8 },
    ],
  },
  {
    id: 'change-password',
    label: 'Change password',
    route: '/change-password',
    group: 'Account',
    image: changePasswordImage,
    description: 'Account security folio with current and new password fields.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Open profile', target: 'profile', x: 15, y: 46, width: 13, height: 8 },
      { label: 'Change password', target: 'profile', x: 35, y: 73, width: 15, height: 9 },
      { label: 'Cancel', target: 'profile', x: 50, y: 73, width: 8, height: 8 },
    ],
  },
  {
    id: 'terms',
    label: 'Terms of service',
    route: '/terms',
    group: 'Reference',
    image: termsImage,
    description: 'Bound legal folio with table of contents and readable service terms.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Sign in', target: 'login', x: 84, y: 2, width: 8, height: 7 },
      { label: 'Return home', target: 'home', x: 8, y: 2, width: 13, height: 7 },
    ],
  },
  {
    id: 'privacy',
    label: 'Privacy policy',
    route: '/privacy',
    group: 'Reference',
    image: privacyImage,
    description: 'Tabbed archival privacy ledger with plain-language data practices.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Sign in', target: 'login', x: 87, y: 2, width: 8, height: 7 },
      { label: 'Return home', target: 'home', x: 4, y: 2, width: 13, height: 7 },
    ],
  },
  {
    id: 'not-found',
    label: 'Page not found',
    route: '/:pathMatch(.*)*',
    group: 'Reference',
    image: notFoundImage,
    description: 'Missing-page atlas with a torn map corner and return actions.',
    hotspots: [
      ...globalNavHotspots,
      { label: 'Return home', target: 'home', x: 60, y: 50, width: 17, height: 9 },
      { label: 'Explore stories', target: 'game-scenario', x: 60, y: 59, width: 17, height: 9 },
      { label: 'Sign in', target: 'login', x: 87, y: 2, width: 8, height: 7 },
    ],
  },
]

const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const showHotspots = ref(false)
const imageLoaded = ref(false)

const screenIds = new Set<ScreenId>(screens.map((screen) => screen.id))

const currentId = computed<ScreenId>(() => {
  const value = route.params.screen
  const id = Array.isArray(value) ? value[0] : value
  return id && screenIds.has(id as ScreenId) ? (id as ScreenId) : 'home'
})

const currentIndex = computed(() => screens.findIndex((screen) => screen.id === currentId.value))
const currentScreen = computed(() => screens[currentIndex.value] ?? screens[0])
const groups = ['Discover', 'Account', 'Story', 'Library', 'Reference'] as const

function navigateTo(id: ScreenId) {
  menuOpen.value = false
  imageLoaded.value = false
  router.push({ name: 'mockup', params: { screen: id } })
}

function moveScreen(direction: -1 | 1) {
  const nextIndex = (currentIndex.value + direction + screens.length) % screens.length
  navigateTo(screens[nextIndex].id)
}

function handleKeyboard(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  if (target?.matches('input, textarea, select')) return

  if (event.key === 'ArrowLeft') moveScreen(-1)
  if (event.key === 'ArrowRight') moveScreen(1)
  if (event.key.toLowerCase() === 'm') menuOpen.value = !menuOpen.value
  if (event.key.toLowerCase() === 'h') showHotspots.value = !showHotspots.value
  if (event.key === 'Escape') menuOpen.value = false
}

function preloadAdjacentScreens() {
  const indexes = [
    (currentIndex.value - 1 + screens.length) % screens.length,
    (currentIndex.value + 1) % screens.length,
  ]

  for (const index of indexes) {
    const image = new Image()
    image.src = screens[index].image
  }
}

watch(currentId, () => {
  imageLoaded.value = false
  preloadAdjacentScreens()
})

onMounted(() => {
  window.addEventListener('keydown', handleKeyboard)
  preloadAdjacentScreens()
  if (!route.params.screen) {
    router.replace({ name: 'mockup', params: { screen: 'home' } })
  }
})

onUnmounted(() => window.removeEventListener('keydown', handleKeyboard))
</script>

<template>
  <main class="prototype-shell" :class="{ 'show-hotspots': showHotspots }">
    <div class="prototype-stage" aria-live="polite">
      <Transition name="screen-fade" mode="out-in">
        <div :key="currentScreen.id" class="screen-frame">
          <img
            class="screen-image"
            :class="{ loaded: imageLoaded }"
            :src="currentScreen.image"
            :alt="currentScreen.description"
            draggable="false"
            @load="imageLoaded = true"
          />

          <button
            v-for="hotspot in currentScreen.hotspots"
            :key="`${currentScreen.id}-${hotspot.label}-${hotspot.target}`"
            class="screen-hotspot"
            :style="{
              left: `${hotspot.x}%`,
              top: `${hotspot.y}%`,
              width: `${hotspot.width}%`,
              height: `${hotspot.height}%`,
            }"
            :aria-label="`${hotspot.label}. Opens ${screens.find((screen) => screen.id === hotspot.target)?.label}.`"
            @click="navigateTo(hotspot.target)"
          >
            <span>{{ hotspot.label }}</span>
          </button>
        </div>
      </Transition>
    </div>

    <button
      class="menu-trigger prototype-control"
      type="button"
      :aria-expanded="menuOpen"
      aria-controls="prototype-screen-menu"
      @click="menuOpen = !menuOpen"
    >
      <span class="menu-trigger-mark" aria-hidden="true">☰</span>
      <span>Screens</span>
      <span class="screen-count">{{ currentIndex + 1 }}/{{ screens.length }}</span>
    </button>

    <div class="route-plaque prototype-control">
      <span>{{ currentScreen.label }}</span>
      <code>{{ currentScreen.route }}</code>
    </div>

    <Transition name="drawer-fade">
      <aside
        v-if="menuOpen"
        id="prototype-screen-menu"
        class="screen-drawer"
        aria-label="Prototype screens"
      >
        <div class="drawer-header">
          <div>
            <p>GenQuest prototype</p>
            <span>Choose any screen</span>
          </div>
          <button type="button" aria-label="Close screen menu" @click="menuOpen = false">×</button>
        </div>

        <div class="drawer-scroll">
          <section v-for="group in groups" :key="group" class="drawer-group">
            <h2>{{ group }}</h2>
            <button
              v-for="screen in screens.filter((item) => item.group === group)"
              :key="screen.id"
              type="button"
              :class="{ active: screen.id === currentScreen.id }"
              @click="navigateTo(screen.id)"
            >
              <span>{{ screen.label }}</span>
              <code>{{ screen.route }}</code>
            </button>
          </section>
        </div>

        <div class="drawer-footer">
          <button type="button" @click="showHotspots = !showHotspots">
            {{ showHotspots ? 'Hide' : 'Show' }} clickable areas <kbd>H</kbd>
          </button>
          <p><kbd>←</kbd><kbd>→</kbd> move between screens <kbd>M</kbd> menu</p>
        </div>
      </aside>
    </Transition>

    <nav class="prototype-pager prototype-control" aria-label="Screen pagination">
      <button type="button" aria-label="Previous screen" @click="moveScreen(-1)">←</button>
      <span>{{ currentScreen.label }}</span>
      <button type="button" aria-label="Next screen" @click="moveScreen(1)">→</button>
    </nav>
  </main>
</template>

<style scoped>
.prototype-shell {
  --ink: #251c15;
  --paper: #f4ead5;
  --paper-deep: #e7d4b4;
  --oxblood: #792d2d;
  --walnut: #211711;
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  min-height: 100dvh;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 35%, #493323 0, #261a13 52%, #130e0a 100%);
  color: var(--ink);
  font-family: Georgia, 'Times New Roman', serif;
}

.prototype-shell::after {
  position: fixed;
  inset: 0;
  pointer-events: none;
  content: '';
  box-shadow: inset 0 0 90px rgb(0 0 0 / 0.42);
}

.prototype-stage {
  display: grid;
  width: 100vw;
  height: 100dvh;
  place-items: center;
}

.screen-frame {
  position: relative;
  width: min(100vw, 177.683dvh);
  aspect-ratio: 1672 / 941;
  overflow: hidden;
  background: #2a1c13;
  box-shadow: 0 30px 90px rgb(0 0 0 / 0.46);
}

.screen-image {
  display: block;
  width: 100%;
  height: 100%;
  user-select: none;
  object-fit: contain;
  opacity: 0;
  transition: opacity 320ms ease;
}

.screen-image.loaded {
  opacity: 1;
}

.screen-hotspot {
  position: absolute;
  z-index: 2;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.screen-hotspot:focus-visible,
.show-hotspots .screen-hotspot {
  border: 2px solid #f6e4bd;
  outline: 2px solid var(--oxblood);
  outline-offset: -4px;
  background: rgb(121 45 45 / 0.14);
}

.screen-hotspot span {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 6px);
  max-width: 180px;
  padding: 5px 8px;
  transform: translateX(-50%);
  border: 1px solid #a57f55;
  background: #f8eedb;
  box-shadow: 0 4px 14px rgb(27 18 12 / 0.28);
  color: #4f211f;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 11px;
  font-weight: 650;
  line-height: 1.2;
  opacity: 0;
  pointer-events: none;
  white-space: nowrap;
}

.screen-hotspot:hover span,
.screen-hotspot:focus-visible span,
.show-hotspots .screen-hotspot span {
  opacity: 1;
}

.prototype-control {
  position: fixed;
  z-index: 20;
  border: 1px solid rgb(235 213 176 / 0.55);
  background: rgb(34 23 16 / 0.94);
  box-shadow: 0 12px 36px rgb(0 0 0 / 0.35);
  color: #f8ecd6;
  font-family: ui-sans-serif, system-ui, sans-serif;
}

.menu-trigger {
  bottom: 16px;
  left: 16px;
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 9px;
  padding: 0 12px;
  cursor: pointer;
}

.menu-trigger:hover,
.prototype-pager button:hover {
  background: #5e2928;
}

.menu-trigger-mark {
  font-size: 17px;
}

.screen-count {
  color: #cdb892;
  font-size: 12px;
}

.route-plaque {
  bottom: 16px;
  left: 160px;
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 12px;
  padding: 0 13px;
}

.route-plaque span {
  font-size: 13px;
  font-weight: 650;
}

.route-plaque code {
  color: #cdb892;
  font-size: 11px;
}

.prototype-pager {
  right: 16px;
  bottom: 16px;
  display: grid;
  grid-template-columns: 44px minmax(140px, auto) 44px;
  min-height: 44px;
  align-items: center;
}

.prototype-pager button {
  align-self: stretch;
  border: 0;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 20px;
}

.prototype-pager span {
  padding: 0 12px;
  text-align: center;
  font-size: 12px;
}

.screen-drawer {
  position: fixed;
  z-index: 30;
  top: 12px;
  bottom: 12px;
  left: 12px;
  display: grid;
  width: min(380px, calc(100vw - 24px));
  grid-template-rows: auto 1fr auto;
  overflow: hidden;
  border: 1px solid #a98c64;
  background: #f5ead6;
  box-shadow: 24px 20px 70px rgb(0 0 0 / 0.48);
  color: #271c14;
  font-family: ui-sans-serif, system-ui, sans-serif;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 19px 18px 16px;
  border-bottom: 1px solid #cbb893;
  background: #ead9bb;
}

.drawer-header p {
  margin: 0;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 22px;
}

.drawer-header span {
  display: block;
  margin-top: 3px;
  color: #715d49;
  font-size: 12px;
}

.drawer-header button {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border: 1px solid #9c7b56;
  background: transparent;
  color: #6c2725;
  cursor: pointer;
  font-family: Georgia, serif;
  font-size: 27px;
}

.drawer-scroll {
  overflow-y: auto;
  padding: 15px 14px 22px;
  scrollbar-color: #9c7b56 transparent;
  scrollbar-width: thin;
}

.drawer-group + .drawer-group {
  margin-top: 18px;
}

.drawer-group h2 {
  margin: 0 5px 7px;
  color: #7b2c2a;
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 0.04em;
}

.drawer-group button {
  display: grid;
  width: 100%;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 10px 10px;
  border: 0;
  border-bottom: 1px solid #d9c9aa;
  background: transparent;
  color: #2a2017;
  cursor: pointer;
  text-align: left;
}

.drawer-group button:hover,
.drawer-group button.active {
  background: #ead9bb;
}

.drawer-group button.active {
  box-shadow: inset 3px 0 #7b2c2a;
}

.drawer-group button span {
  font-size: 13px;
  font-weight: 650;
}

.drawer-group button code {
  overflow: hidden;
  max-width: 150px;
  color: #7a6854;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-footer {
  padding: 13px 14px 15px;
  border-top: 1px solid #cbb893;
  background: #ead9bb;
}

.drawer-footer button {
  width: 100%;
  min-height: 40px;
  border: 1px solid #7d3a35;
  background: #7b2c2a;
  color: #fff4df;
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
}

.drawer-footer p {
  margin: 11px 0 0;
  color: #6a5947;
  font-size: 10px;
  text-align: center;
}

kbd {
  display: inline-grid;
  min-width: 19px;
  min-height: 18px;
  place-items: center;
  margin-inline: 2px;
  border: 1px solid #9d8564;
  background: #f9efd9;
  color: #4b3829;
  font-family: ui-monospace, monospace;
  font-size: 9px;
}

.screen-fade-enter-active,
.screen-fade-leave-active {
  transition: opacity 220ms ease, transform 220ms ease;
}

.screen-fade-enter-from {
  opacity: 0;
  transform: translateX(12px);
}

.screen-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}

.drawer-fade-enter-active,
.drawer-fade-leave-active {
  transition: opacity 180ms ease, transform 220ms ease;
}

.drawer-fade-enter-from,
.drawer-fade-leave-to {
  opacity: 0;
  transform: translateX(-18px);
}

@media (max-width: 700px) {
  .route-plaque {
    display: none;
  }

  .prototype-pager {
    right: 8px;
    bottom: 8px;
    grid-template-columns: 42px 42px;
  }

  .prototype-pager span {
    display: none;
  }

  .menu-trigger {
    bottom: 8px;
    left: 8px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .screen-image,
  .screen-fade-enter-active,
  .screen-fade-leave-active,
  .drawer-fade-enter-active,
  .drawer-fade-leave-active {
    transition: none;
  }
}
</style>

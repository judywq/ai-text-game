export const NATIVE_LANGUAGE_UNSET = '__unset__' as const

export const NATIVE_LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'fr', label: 'French' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
] as const

export type NativeLanguageCode = (typeof NATIVE_LANGUAGE_OPTIONS)[number]['value']

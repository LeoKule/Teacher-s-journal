// Токен живёт в httpOnly cookie на бэке — JS его не видит и не должен.
// В storage держим только UI-метаданные, чтобы не дёргать /profile на каждой загрузке.

const META_KEYS = ['user_role', 'user_id', 'full_name', 'email']

export const getUserRole = () =>
  localStorage.getItem('user_role') || sessionStorage.getItem('user_role')

export const clearAuthData = () => {
  META_KEYS.forEach((key) => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })
}

export const storeAuthData = (authData, rememberMe = true) => {
  const storage = rememberMe ? localStorage : sessionStorage
  const otherStorage = rememberMe ? sessionStorage : localStorage

  META_KEYS.forEach((key) => otherStorage.removeItem(key))

  storage.setItem('user_role', authData.user_role)
  storage.setItem('user_id', String(authData.user_id))
  storage.setItem('full_name', authData.full_name)
  storage.setItem('email', authData.email)
}

// Реальная сессия = httpOnly cookie на бэке. Здесь — только UI-эвристика для guard'ов.
// Если cookie протухло, бэк ответит 401 → axios сделает refresh либо редирект на логин.
export const hasUsableSession = () => !!getUserRole()

export const getCsrfToken = () => {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : null
}

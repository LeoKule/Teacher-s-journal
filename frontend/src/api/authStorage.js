const AUTH_KEYS = ['access_token', 'user_role', 'user_id', 'full_name', 'email']

export const getAccessToken = () =>
  localStorage.getItem('access_token') || sessionStorage.getItem('access_token')

export const getUserRole = () =>
  localStorage.getItem('user_role') || sessionStorage.getItem('user_role')

export const clearAuthData = () => {
  AUTH_KEYS.forEach((key) => {
    localStorage.removeItem(key)
    sessionStorage.removeItem(key)
  })
}

export const storeAuthData = (authData, rememberMe = true) => {
  const storage = rememberMe ? localStorage : sessionStorage
  const otherStorage = rememberMe ? sessionStorage : localStorage

  AUTH_KEYS.forEach((key) => otherStorage.removeItem(key))

  storage.setItem('access_token', authData.access_token)
  storage.setItem('user_role', authData.user_role)
  storage.setItem('user_id', String(authData.user_id))
  storage.setItem('full_name', authData.full_name)
  storage.setItem('email', authData.email)
}

export const updateStoredAccessToken = (accessToken) => {
  if (localStorage.getItem('access_token')) {
    localStorage.setItem('access_token', accessToken)
    return
  }

  if (sessionStorage.getItem('access_token')) {
    sessionStorage.setItem('access_token', accessToken)
    return
  }

  localStorage.setItem('access_token', accessToken)
}

const decodeJwtPayload = (token) => {
  try {
    const base64 = token.split('.')[1]
    if (!base64) return null

    const normalized = base64.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + ((4 - normalized.length % 4) % 4), '=')
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

export const isTokenExpired = (token) => {
  if (!token) return true

  const payload = decodeJwtPayload(token)
  if (!payload?.exp) return true

  return payload.exp * 1000 <= Date.now() + 5000
}

export const hasUsableSession = () => !isTokenExpired(getAccessToken())

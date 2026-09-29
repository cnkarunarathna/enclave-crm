// Tiny pub/sub so the API layer (plain TS) can tell React that the session ended.

type Listener = () => void
const listeners = new Set<Listener>()

/** Subscribe; returns an unsubscribe function (handy as a useEffect cleanup). */
export function onSessionExpired(listener: Listener) {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

export function emitSessionExpired() {
  listeners.forEach((listener) => listener())
}

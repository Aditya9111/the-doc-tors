import { useEffect, useState } from 'react'

export default function Health() {
  const [health, setHealth] = useState<any>(null)
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const load = async () => {
    setLoading(true)
    setError(null)
    try {
      const [h, s] = await Promise.all([
        fetch('/api/health').then(r => r.json()),
        fetch('/api/stats').then(r => r.json())
      ])
      setHealth(h)
      setStats(s)
    } catch (e: any) { setError(e.message) } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])
  
  return (
    <div>
      <h2>Health & Stats</h2>
      <button onClick={load} disabled={loading}>Refresh</button>
      {loading && <p>Loading...</p>}
      {error && <pre style={{ color: 'crimson' }}>{error}</pre>}
      {health && (<>
        <h3>Health</h3>
        <pre>{JSON.stringify(health, null, 2)}</pre>
      </>)}
      {stats && (<>
        <h3>Stats</h3>
        <pre>{JSON.stringify(stats, null, 2)}</pre>
      </>)}
    </div>
  )
}



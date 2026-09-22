import { useState } from 'react';

async function request(url, options) {
  const response = await fetch(url, options);
  const body = await response.json();
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'Unable to load weather. Please try again.');
  return body;
}

export default function App() {
  const [city, setCity] = useState('');
  const [readings, setReadings] = useState([]);
  const [searched, setSearched] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  async function load(shouldFetch) {
    const query = city.trim();
    if (!query || busy) return;
    setBusy(true); setError(''); setNotice('');
    let saved = false;
    try {
      if (shouldFetch) {
        await request(`/weather/fetch?city=${encodeURIComponent(query)}`, { method: 'POST' });
        saved = true;
      }
      const history = await request(`/weather/${encodeURIComponent(query)}`);
      setReadings(history); setSearched(query);
      setNotice(saved ? 'Current conditions saved.' : 'Saved readings loaded.');
    } catch (err) {
      setError(saved ? 'Reading saved, but history could not load. Select View history to try again.' : err.message);
    } finally { setBusy(false); }
  }

  const latest = readings[0];
  return <main>
    <header><a className="brand" href="/">◒ <span>WEATHER JOURNAL</span></a><span className="source">Powered by Open-Meteo</span></header>
    <section className="intro"><div className="eyebrow">A MOMENT, MEASURED</div><h1>The weather.<br/><em>Worth keeping.</em></h1><p>Check the conditions in any city and keep a little history.<br className="desktop"/> One place, one reading at a time.</p></section>
    <section className="search-panel" aria-label="Find weather">
      <form onSubmit={event => { event.preventDefault(); load(true); }}>
        <label htmlFor="city">Where are we looking?</label>
        <div className="controls"><input id="city" value={city} onChange={event => setCity(event.target.value)} placeholder="Enter a city, e.g. Timișoara" maxLength={100} required disabled={busy}/><button disabled={busy || !city.trim()} type="submit">{busy ? 'Loading…' : 'Fetch & save'} <span aria-hidden="true">↗</span></button><button className="secondary" type="button" disabled={busy || !city.trim()} onClick={() => load(false)}>View history</button></div>
      </form>
      <p className="hint">Current conditions only. Every fetch adds a new reading.</p>
      {error && <p role="alert" className="error">{error}</p>}
      <p role="status" className="notice">{notice}</p>
    </section>
    <section className="history" aria-busy={busy}>
      <div className="section-heading"><h2>{searched ? `Readings for ${latest?.city || searched}` : 'Your weather history'}</h2><span>{readings.length} {readings.length === 1 ? 'reading' : 'readings'}</span></div>
      {latest && <div className="latest"><div><div className="eyebrow">LATEST SAVED</div><strong>{latest.temperature}°<small>C</small></strong><p>{latest.description}</p></div><div className="wind"><span>Wind speed</span><b>{latest.wind_speed} <small>km/h</small></b></div></div>}
      {readings.length ? <div className="table-wrap"><table><thead><tr><th>Fetched at</th><th>Conditions</th><th>Temperature</th><th>Wind</th></tr></thead><tbody>{readings.map(reading => <tr key={reading.id}><td><time dateTime={reading.fetched_at}>{new Date(reading.fetched_at).toLocaleString()}</time></td><td>{reading.description}</td><td>{reading.temperature} °C</td><td>{reading.wind_speed} km/h</td></tr>)}</tbody></table><p className="hint">Most recent first · Times shown in your local timezone</p></div> : <div className="empty"><span aria-hidden="true">☀</span><h3>{searched ? 'No saved readings yet' : 'A fresh start, whatever the weather.'}</h3><p>Enter a city above and fetch its current conditions.<br/>Your saved readings will appear here.</p></div>}
    </section>
    <footer><span>A small record of the world outside.</span><a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Weather data by Open-Meteo ↗</a></footer>
  </main>;
}

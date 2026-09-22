import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { test, expect, vi, afterEach } from 'vitest';
import App from './App';

afterEach(() => vi.unstubAllGlobals());
const reading = {id: 1, city: 'Paris', temperature: 22.4, wind_speed: 14.2, description: 'Overcast', fetched_at: '2026-01-01T10:00:00Z'};
const result = body => ({ ok: true, json: async () => body });

test('fetches a city, saves it, and renders stored readings', async () => {
  const fetch = vi.fn().mockResolvedValueOnce(result(reading)).mockResolvedValueOnce(result([reading]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  await userEvent.type(screen.getByLabelText('Where are we looking?'), 'Paris');
  await userEvent.click(screen.getByRole('button', {name: /Fetch & save/}));
  expect(await screen.findByText('Readings for Paris')).toBeInTheDocument();
  expect(screen.getByRole('cell', {name: '22.4 °C'})).toBeInTheDocument();
  expect(fetch).toHaveBeenNthCalledWith(1, '/weather/fetch?city=Paris', {method: 'POST'});
  expect(fetch).toHaveBeenNthCalledWith(2, '/weather/Paris', undefined);
});

test('loads history without fetching new conditions', async () => {
  const fetch = vi.fn().mockResolvedValue(result([]));
  vi.stubGlobal('fetch', fetch);
  render(<App />);
  await userEvent.type(screen.getByLabelText('Where are we looking?'), 'New York');
  await userEvent.click(screen.getByRole('button', {name: 'View history'}));
  expect(await screen.findByText('No saved readings yet')).toBeInTheDocument();
  expect(fetch).toHaveBeenCalledExactlyOnceWith('/weather/New%20York', undefined);
});

test('shows provider errors and allows another attempt', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok: false, json: async () => ({detail: 'City not found: nowhere'})}));
  render(<App />);
  await userEvent.type(screen.getByLabelText('Where are we looking?'), 'nowhere');
  await userEvent.click(screen.getByRole('button', {name: /Fetch & save/}));
  expect(await screen.findByRole('alert')).toHaveTextContent('City not found: nowhere');
  await waitFor(() => expect(screen.getByRole('button', {name: /Fetch & save/})).toBeEnabled());
});

test('prevents duplicate submissions while fetching', async () => {
  let resolve;
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(new Promise(r => {resolve = r;})));
  render(<App />);
  await userEvent.type(screen.getByLabelText('Where are we looking?'), 'Paris');
  await userEvent.click(screen.getByRole('button', {name: /Fetch & save/}));
  expect(screen.getByRole('button', {name: /Loading/})).toBeDisabled();
  expect(screen.getByLabelText('Where are we looking?')).toBeDisabled();
  resolve({ok: false, json: async () => ({detail: 'Unavailable'})});
  await screen.findByRole('alert');
});

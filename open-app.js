(function () {
  'use strict';
  const path = window.location.pathname.split('/').filter(Boolean);
  const parts = path[0] === 'staging' ? path.slice(1) : path;
  const safeId = /^[A-Za-z0-9_-]+$/;
  let appUrl = 'triku://';
  let destination = 'Triku';
  if (parts[0] === 'contests' && safeId.test(parts[1]) &&
      (parts.length === 2 || (parts.length === 3 && parts[2] === 'results'))) {
    appUrl = `triku://contests/${encodeURIComponent(parts[1])}${parts[2] === 'results' ? '/results' : ''}`;
    destination = 'this contest';
  } else if (parts[0] === 'events' && parts.length === 2 && safeId.test(parts[1])) {
    appUrl = `triku://events/${encodeURIComponent(parts[1])}`;
    destination = 'this event';
  } else if (parts.length === 1 && parts[0] === 'wallet') {
    appUrl = 'triku://wallet';
    destination = 'your wallet';
  } else if (parts.length === 2 && parts[0] === 'verification' && parts[1] === 'aadhaar') {
    appUrl = 'triku://verification/aadhaar';
    destination = 'verification';
  }
  const label = document.querySelector('[data-destination]');
  const button = document.querySelector('[data-open-app]');
  if (label) label.textContent = destination;
  if (button) button.setAttribute('href', appUrl);
}());

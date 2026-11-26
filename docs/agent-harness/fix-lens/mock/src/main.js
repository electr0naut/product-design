import { analyse } from './analyse.js';
import { render } from './render.js';

const input = document.querySelector('#paste');
// The last analysis and the selected order live in memory only.
let result = null;
const show = orderId => render(result, orderId, { pick: show, clear: () => show(null) });
document.querySelector('#decode-button').addEventListener('click', () => {
  result = analyse(input.value);
  show(null);
});

// Theme: follows the system setting until the button is used. The choice is kept in memory only
// (nothing is stored), so a reload returns to the system setting.
const themeButton = document.querySelector('#theme-button');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)');
let dark = systemDark.matches;
const label = () => { themeButton.textContent = dark ? 'Light theme' : 'Dark theme'; };
label();
themeButton.addEventListener('click', () => {
  dark = !dark;
  document.documentElement.className = dark ? 'theme-dark' : 'theme-light';
  label();
});

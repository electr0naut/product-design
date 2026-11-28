import { analyse } from './analyse.js';
import { render } from './render.js';

const input = document.querySelector('#paste');
// The last analysis, the selected order and the chosen filters live in memory only.
let result = null;
const view = { orderId: null, filters: {} };
const handlers = {
  pick: orderId => { view.orderId = orderId; show(); },
  clear: () => { view.orderId = null; show(); },
  setFilter: (key, value) => {
    if (key === null) view.filters = {}; else view.filters[key] = value;
    show();
  },
};
function show() { render(result, view, handlers); }
document.querySelector('#decode-button').addEventListener('click', () => {
  result = analyse(input.value);
  view.orderId = null;
  view.filters = {};
  show();
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

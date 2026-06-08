import {
  Cookies,
  initAll,
} from "@nationalarchives/frontend/nationalarchives/all.mjs";

const cookiesDomain =
  document.documentElement.getAttribute("data-cookiesdomain");

const initializeCookies = (domain) => new Cookies({ domain });

if (cookiesDomain) {
  initializeCookies(cookiesDomain);
}

initAll();

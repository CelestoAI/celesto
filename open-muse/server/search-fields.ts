import { SENSITIVE_TARGET } from "./sensitive-target.js";

export const UNSAFE_SEARCH_AUTOCOMPLETE = /(?:^|\s)(?:section-\S+|shipping|billing|email|tel\S*|cc-\S*|.*password|one-time-code|username)(?:\s|$)/i;

export function isSearchFieldCandidate(target: {
    role: string;
    name: string;
}): boolean {
    if (!["searchbox", "textbox"].includes(target.role)) return false;

    // Do not treat sensitive fields as public search inputs.
    if (
        SENSITIVE_TARGET.test(target.name) ||
        /\b(?:email|phone|verification)\b/i.test(target.name)
    ) {
        return false;
    }

  return (
    target.role === "searchbox" ||
    /\bsearch\b/i.test(target.name)
  );
}

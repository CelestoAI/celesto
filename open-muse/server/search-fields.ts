export function isSearchFieldCandidate(target: {
    role: string;
    name: string;
}): boolean {
    if (!["searchbox", "textbox"].includes(target.role)) return false;

    // Do not treat sensitive fields as public search inputs.
    if (
        /\b(password|passcode|otp|verification|credit card|payment|email|phone)\b/i.test(
        target.name,
        )
    ) {
        return false;
    }

  return (
    target.role === "searchbox" ||
    /\bsearch\b/i.test(target.name)
  );
}
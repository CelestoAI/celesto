import type { ExecutableBrowserOperation } from "./browser-operations.js";

export type ActionDecision = "allow" | "confirm" | "deny";

export interface ActionPolicyResult {
  decision: ActionDecision;
  reason: string;
}

const SENSITIVE_TARGET = /\b(?:card|credential|cvc|cvv|otp|passcode|password|payment|secret|token|expir(?:y|ation)|(?:security|verification)[\s._/-]*code|mm[\s._/-]*yy)\b/i;

/**
 * Classify the effect, not the Playwright primitive. Validation of URLs, refs,
 * and field types happens before this function; this function only decides
 * whether a valid operation may flow, must pause, or is never model-operated.
 */
export function decideBrowserAction(operation: ExecutableBrowserOperation): ActionPolicyResult {
  switch (operation.kind) {
    case "observe":
    case "extract":
    case "scroll":
    case "navigate":
    case "follow_link":
    case "search":
      return { decision: "allow", reason: "This public research action does not create external state." };
    case "fill":
      if (SENSITIVE_TARGET.test(`${operation.target.role} ${operation.target.name}`)) {
        return { decision: "deny", reason: "Use Take control to enter passwords, payment details, codes, or other secrets." };
      }
      return { decision: "confirm", reason: "Filling this field may change information sent to the website." };
    case "click":
    case "select":
    case "keypress":
      return { decision: "confirm", reason: "This website interaction may create or change external state." };
  }
}

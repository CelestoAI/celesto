from enum import StrEnum


class DocumentType(StrEnum):
    COVER_LETTER = "cover-letter"
    EVIDENCE = "evidence"
    ID_PROOF = "id-proof"
    LETTER_OF_RECOMMENDATION = "letter-of-recommendation"
    OTHER = "other"
    PASSPORT = "passport"
    PROOF_OF_ADDRESS = "proof-of-address"
    RESUME = "resume"

    def __str__(self) -> str:
        return str(self.value)

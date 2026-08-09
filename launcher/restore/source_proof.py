"""C4-II-B1 launcher-private binding of retained A1 source proof.

This module does not select a path, create Restore state, create a safety copy or
mutate the working database. It only proves that the already-open C4-I
:class:`HeldSource` is still the exact source A1 accepted earlier.

The proof is deliberately performed against the same held descriptor that the
engine subsequently passes to ``stage_source``. A path-only pre-check followed by
a later re-open would leave the substitution window B1 exists to close.
"""

from __future__ import annotations

from launcher.restore.contracts import ExpectedSourceProof
from launcher.restore.staging import HeldSource, SourceRejectedError


class SourceProofMismatchError(RuntimeError):
    """The selected source no longer matches the retained A1 proof."""


def bind_expected_source_proof(
    held: HeldSource,
    expected: ExpectedSourceProof,
) -> None:
    """Prove A1 identity + full SHA-256 on the exact held descriptor.

    Identity and self-containment are proved before and after the full digest
    read. The digest byte count must equal the held identity size. Any inability
    to prove the source is collapsed to this one launcher-private mismatch class;
    callers render only the fixed ``SOURCE_CHANGED`` user-safe message.
    """

    try:
        if held.identity != expected.source_identity:
            raise SourceProofMismatchError

        held.revalidate()
        held.assert_still_self_contained()

        digest, byte_count = held.digest()
        if byte_count != held.size_bytes or digest != expected.sha256:
            raise SourceProofMismatchError

        held.revalidate()
        held.assert_still_self_contained()
    except SourceProofMismatchError:
        raise
    except SourceRejectedError as exc:
        raise SourceProofMismatchError from exc

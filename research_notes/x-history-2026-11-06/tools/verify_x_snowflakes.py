#!/usr/bin/env python3
"""Check times encoded in selected X Snowflake IDs, without network requests.

WARNING: This confirms ID creation time only; it cannot verify text,
edit history, account authorship, or authenticity of an archived screenshot.
"""

from datetime import datetime, timezone

X_EPOCH_MS = 1288834974657

POSTS = {
    "snoorrason_top5": (2110285369748963671, "2026-10-14T08:23:34+00:00"),
    "ec_unoxx_privacy_four": (2008147229325013019, "2026-01-05T12:03:03+00:00"),
    "sbet_lookonchain": (2011736650054062085, "2026-01-15T09:46:08+00:00"),
    "flydartball_platform": (1935081943001088030, "2025-06-17T21:07:41+00:00"),
    "jydyjyd_exit": (2115072247618531466, "2026-10-27T13:24:54+00:00"),
    "cypya_top5": (2111149784858042762, "2026-10-16T17:38:26+00:00"),
    "jydyjyd_copy": (2112913244058755159, "2026-10-21T14:25:48+00:00"),
    "betint_maduro": (2007351724185461007, "2026-01-03T07:22:00+00:00"),
    "andrey_group38": (2034030676589351244, "2026-03-17T22:14:38+00:00"),
    "cashy_yes_alert": (2027633061949501704, "2026-02-28T06:32:48+00:00"),
    "flydartball_loss": (1935769781669437727, "2025-06-19T18:40:55+00:00"),
    "car_correction": (2021095225393873035, "2026-02-10T05:33:46+00:00"),
}


def decode_post_time(post_id: int) -> datetime:
    timestamp_ms = (post_id >> 22) + X_EPOCH_MS
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)


def main() -> None:
    for label, (post_id, expected_time) in POSTS.items():
        actual = decode_post_time(post_id)
        expected = datetime.fromisoformat(expected_time)
        if actual.replace(microsecond=0) != expected:
            raise SystemExit(
                f"MISMATCH {label}: {actual.isoformat()} != {expected.isoformat()}"
            )
        print(f"OK {label}: {actual.isoformat()}")
    print(f"Verified {len(POSTS)} encoded timestamps. Post content NOT verified.")


if __name__ == "__main__":
    main()

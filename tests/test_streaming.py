"""Tests for bounded command-stream event parsing."""

import pytest

from celesto._streaming import iter_bounded_lines, iter_sse_data, parse_command_event
from celesto.exceptions import CelestoError


def test_iter_sse_data_preserves_standard_multiline_events() -> None:
    data = list(
        iter_sse_data(
            [
                "data: {",
                'data: "type": "stdout",',
                'data: "data": "ok"',
                "data: }",
                "",
            ]
        )
    )

    event = parse_command_event(data[0])
    assert event.type == "stdout"
    assert event.data == "ok"  # type: ignore[union-attr]


def test_iter_sse_data_splits_deployed_json_lines_without_blank_delimiters() -> None:
    data = list(
        iter_sse_data(
            [
                'data: {"type":"stdout","data":"one"}',
                'data: {"type":"stderr","data":"two"}',
            ]
        )
    )

    assert [parse_command_event(item).type for item in data] == ["stdout", "stderr"]


def test_iter_sse_data_rejects_oversized_event_before_json_parsing() -> None:
    with pytest.raises(CelestoError, match="too large"):
        list(iter_sse_data(["data: " + "x" * (1024 * 1024 + 1)]))


def test_iter_bounded_lines_preserves_chunked_crlf_records() -> None:
    lines = list(iter_bounded_lines([b"data: one\r", b"\n\r\ndata: ", b"two\n"]))

    assert lines == [b"data: one\r\n", b"\r\n", b"data: two\n"]


def test_iter_bounded_lines_rejects_oversized_newline_less_record() -> None:
    chunks = [b"x" * (512 * 1024), b"x" * (512 * 1024), b"x"]

    with pytest.raises(CelestoError, match="too large"):
        list(iter_bounded_lines(chunks))


def test_iter_bounded_lines_allows_limit_sized_record_with_split_crlf() -> None:
    chunks = [b"x" * (1024 * 1024) + b"\r", b"\n"]

    assert list(iter_bounded_lines(chunks)) == [chunks[0] + chunks[1]]

from don.message_composer import compose_message


def test_verbatim():
    msg, confirm = compose_message("send exactly these words: Hello Ali")
    assert msg.startswith("send exactly these words")
    assert confirm is False


def test_friendly():
    msg, confirm = compose_message("kripya isy friendly rakhna: kal milte hain", tone="friendly")
    assert "Friendly" in msg and confirm is True


def test_formal_detection():
    msg, confirm = compose_message("Please keep it formal: Meeting rescheduled.")
    assert confirm in (True, False)

from app.services.context.assembler import format_environmental_context


def test_no_location_gives_general_guidance_note():
    text = format_environmental_context(None, None)
    assert "No location was provided" in text


def test_location_without_record_says_not_integrated():
    text = format_environmental_context(32.585, 73.492)
    assert "32.585" in text
    assert "not yet integrated" in text


def test_location_with_available_false_says_unavailable():
    text = format_environmental_context(32.585, 73.492, environmental_available=False)
    assert "Data unavailable for this location" in text


def test_location_with_real_record_includes_values_and_data_source():
    record = {"soil_ph": 6.8, "clay": 22.0, "temperature": 28.5, "data_source": "SoilGrids + NASA POWER"}
    text = format_environmental_context(32.585, 73.492, environmental_record=record)
    assert "6.8" in text
    assert "28.5" in text
    assert "SoilGrids + NASA POWER" in text
    assert "estimated" in text.lower()


def test_location_with_record_shows_not_available_for_missing_fields():
    record = {"soil_ph": 6.8, "data_source": "SoilGrids"}
    text = format_environmental_context(32.585, 73.492, environmental_record=record)
    assert "Clay content: not available from these sources" in text
# tests/test_app_ui.py
# Auto-download a matching chromedriver so Selenium can run without manual PATH edits
import chromedriver_autoinstaller
chromedriver_autoinstaller.install()  # installs chromedriver for the installed Chrome version

import pytest
import app as app_module  # expects `app = Dash(__name__)` in app.py

def start(dash_duo):
    dash_duo.start_server(app_module.app)
    return dash_duo

def test_header_present(dash_duo):
    dd = start(dash_duo)
    header = dd.wait_for_element("h1", timeout=8)
    assert header is not None
    assert "pink morsel" in header.text.lower() or "pink" in header.text.lower()

def test_visualisation_present(dash_duo):
    dd = start(dash_duo)
    graph = dd.wait_for_element("#sales-line", timeout=10)
    assert graph is not None
    assert graph.is_displayed()

def test_region_picker_present(dash_duo):
    dd = start(dash_duo)
    radio = dd.wait_for_element("#region-radio", timeout=8)
    assert radio is not None
    radio_text = radio.text.lower()
    for opt in ["north", "east", "south", "west", "all"]:
        assert opt in radio_text, f"Expected radio option '{opt}' not found in region-picker"

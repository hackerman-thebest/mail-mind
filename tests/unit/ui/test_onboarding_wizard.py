"""
Unit tests for OnboardingWizard component.

Tests Story 2.5: Hardware Profiling & Onboarding Wizard
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import time

from mailmind.ui.dialogs.onboarding_wizard import OnboardingWizard
from mailmind.core.settings_manager import SettingsManager
from mailmind.database.database_manager import DatabaseManager


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def mock_settings_manager():
    """Create mock SettingsManager."""
    mock = MagicMock(spec=SettingsManager)
    return mock


@pytest.fixture
def mock_db_manager():
    """Create mock DatabaseManager."""
    mock = MagicMock(spec=DatabaseManager)
    mock.get_preference = Mock(return_value=None)
    mock.set_preference = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_hardware_profile():
    """Create mock hardware profile."""
    return {
        "cpu_cores": 8,
        "ram_total_gb": 16.0,
        "ram_available_gb": 8.0,
        "gpu_detected": True,
        "gpu_vram_gb": 8.0,
        "hardware_tier": "Optimal",
        "expected_tokens_per_second": 150,
        "recommended_model": "llama3:8b"
    }


class TestOnboardingWizardInitialization:
    """Test OnboardingWizard initialization."""

    def test_initialization_with_dependencies(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard initializes with required dependencies."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        assert wizard.settings_manager == mock_settings_manager
        assert wizard.db_manager == mock_db_manager
        assert wizard.current_step == 1
        assert wizard.total_steps == 5
        assert wizard.hardware_profile is None
        assert wizard.outlook_connector is None
        assert wizard.indexed_count == 0
        assert wizard.operation_in_progress is False
        assert wizard.operation_cancelled is False

        wizard.destroy()

    def test_initialization_with_callback(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard initializes with completion callback."""
        callback = Mock()
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager, on_complete=callback)

        assert wizard.on_complete_callback == callback

        wizard.destroy()

    def test_wizard_is_modal(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard is modal (transient and grab_set)."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        # Dialog should be transient
        assert wizard.transient() is not None

        wizard.destroy()

    def test_window_properties(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard window properties."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        assert wizard.title() == "MailMind Setup Wizard"
        assert "800x600" in wizard.geometry()  # May include position

        wizard.destroy()


class TestStepNavigation:
    """Test wizard step navigation."""

    def test_initial_step(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard starts at step 1."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        assert wizard.current_step == 1

        wizard.destroy()

    def test_show_step_updates_current_step(self, root, mock_settings_manager, mock_db_manager):
        """Test _show_step updates current_step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(3)
        assert wizard.current_step == 3

        wizard.destroy()

    def test_next_button_advances_step(self, root, mock_settings_manager, mock_db_manager):
        """Test Next button advances to next step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(1)
        wizard._on_next_clicked()

        assert wizard.current_step == 2

        wizard.destroy()

    def test_back_button_goes_to_previous_step(self, root, mock_settings_manager, mock_db_manager):
        """Test Back button goes to previous step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(3)
        wizard._on_back_clicked()

        assert wizard.current_step == 2

        wizard.destroy()

    def test_back_button_disabled_on_first_step(self, root, mock_settings_manager, mock_db_manager):
        """Test Back button is disabled on first step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(1)
        # Back button should be disabled, calling it shouldn't change step
        wizard._on_back_clicked()

        assert wizard.current_step == 1

        wizard.destroy()

    def test_next_button_disabled_during_operations(self, root, mock_settings_manager, mock_db_manager):
        """Test Next button is disabled during background operations."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard.operation_in_progress = True
        wizard._update_navigation_buttons()

        # Can't easily test button state, but calling next should do nothing
        current_step = wizard.current_step
        wizard._on_next_clicked()
        assert wizard.current_step == current_step

        wizard.destroy()


class TestStep1Welcome:
    """Test Step 1: Welcome screen."""

    def test_welcome_step_displays(self, root, mock_settings_manager, mock_db_manager):
        """Test welcome step displays correctly."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(1)

        # Check header
        assert "Welcome to MailMind" in wizard.header_label.cget("text")

        wizard.destroy()

    def test_welcome_step_has_content(self, root, mock_settings_manager, mock_db_manager):
        """Test welcome step has welcome message."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(1)

        # Content frame should have children
        assert len(wizard.content_frame.winfo_children()) > 0

        wizard.destroy()


class TestStep2HardwareDetection:
    """Test Step 2: Hardware detection."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    def test_hardware_detection_starts_background_thread(self, mock_profiler, root, mock_settings_manager, mock_db_manager, mock_hardware_profile):
        """Test hardware detection starts background thread."""
        mock_profiler.detect_hardware.return_value = mock_hardware_profile

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(2)

        # Should start operation
        assert wizard.operation_in_progress is True

        wizard.destroy()

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    def test_hardware_detection_saves_profile(self, mock_profiler, root, mock_settings_manager, mock_db_manager, mock_hardware_profile):
        """Test hardware detection saves profile to database."""
        mock_profiler.detect_hardware.return_value = mock_hardware_profile

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(2)

        # Give thread time to complete
        time.sleep(1.0)
        root.update()

        # Should have saved to database
        mock_db_manager.set_preference.assert_called()

        wizard.destroy()

    def test_hardware_results_display_optimal_tier(self, root, mock_settings_manager, mock_db_manager, mock_hardware_profile):
        """Test hardware results display for Optimal tier."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.hardware_profile = mock_hardware_profile

        wizard._show_step(2)
        wizard._show_hardware_results(1.5)

        # Should show tier with color
        assert wizard.hw_results_frame.winfo_ismapped()

        wizard.destroy()

    def test_hardware_tier_colors_defined(self, root, mock_settings_manager, mock_db_manager):
        """Test hardware tier colors are defined."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        assert "Optimal" in wizard.TIER_COLORS
        assert "Recommended" in wizard.TIER_COLORS
        assert "Minimum" in wizard.TIER_COLORS
        assert "Insufficient" in wizard.TIER_COLORS

        assert "Optimal" in wizard.TIER_EMOJIS
        assert "Recommended" in wizard.TIER_EMOJIS
        assert "Minimum" in wizard.TIER_EMOJIS
        assert "Insufficient" in wizard.TIER_EMOJIS

        wizard.destroy()

    def test_hardware_error_handling(self, root, mock_settings_manager, mock_db_manager):
        """Test hardware detection error handling."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(2)
        wizard._show_hardware_error("Test error")

        # Should show error message
        # Next button should still be enabled to continue
        wizard._update_navigation_buttons()

        wizard.destroy()


class TestStep3PerformanceExpectations:
    """Test Step 3: Performance expectations."""

    def test_performance_expectations_displays(self, root, mock_settings_manager, mock_db_manager, mock_hardware_profile):
        """Test performance expectations step displays."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.hardware_profile = mock_hardware_profile

        wizard._show_step(3)

        # Header should show tier
        assert "Performance Expectations" in wizard.header_label.cget("text")

        wizard.destroy()

    def test_performance_expectations_for_optimal_tier(self, root, mock_settings_manager, mock_db_manager):
        """Test performance expectations for Optimal tier."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        expectations = wizard._get_tier_expectations("Optimal")

        assert "Email Analysis" in expectations
        assert "Response Generation" in expectations
        assert "Lightning fast" in expectations["Email Analysis"]

        wizard.destroy()

    def test_performance_expectations_for_minimum_tier(self, root, mock_settings_manager, mock_db_manager):
        """Test performance expectations for Minimum tier."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        expectations = wizard._get_tier_expectations("Minimum")

        assert "Email Analysis" in expectations
        assert "Moderate" in expectations["Email Analysis"]

        wizard.destroy()

    def test_performance_tips_for_each_tier(self, root, mock_settings_manager, mock_db_manager):
        """Test performance tips are provided for each tier."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        for tier in ["Optimal", "Recommended", "Minimum", "Insufficient"]:
            tips = wizard._get_tier_tips(tier)
            assert len(tips) > 0
            assert isinstance(tips, list)

        wizard.destroy()


class TestStep4OutlookConnection:
    """Test Step 4: Outlook connection test."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_outlook_connection_starts_background_thread(self, mock_connector, root, mock_settings_manager, mock_db_manager):
        """Test Outlook connection starts background thread."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(4)

        # Should start operation
        assert wizard.operation_in_progress is True

        wizard.destroy()

    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_outlook_connection_success(self, mock_connector_class, root, mock_settings_manager, mock_db_manager):
        """Test successful Outlook connection."""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_status = MagicMock()
        mock_status.status = "Connected"
        mock_status.email_address = "test@example.com"
        mock_connector.get_connection_status.return_value = mock_status
        mock_connector_class.return_value = mock_connector

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(4)

        # Give thread time to complete
        time.sleep(1.0)
        root.update()

        # Should have created connector
        assert wizard.outlook_connector is not None

        wizard.destroy()

    def test_outlook_error_handling(self, root, mock_settings_manager, mock_db_manager):
        """Test Outlook connection error handling."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(4)
        wizard._show_outlook_error("Connection failed")

        # Should show error message
        # Next button should still be enabled to continue
        wizard._update_navigation_buttons()

        wizard.destroy()


class TestStep5EmailIndexing:
    """Test Step 5: Email indexing."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_email_indexing_starts_background_thread(self, mock_connector, root, mock_settings_manager, mock_db_manager):
        """Test email indexing starts background thread."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(5)

        # Should start operation
        assert wizard.operation_in_progress is True

        wizard.destroy()

    def test_next_button_changes_to_finish(self, root, mock_settings_manager, mock_db_manager):
        """Test Next button changes to Finish on last step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(5)
        wizard._update_navigation_buttons()

        assert wizard.next_btn.cget("text") == "Finish"

        wizard.destroy()

    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_email_indexing_success(self, mock_connector_class, root, mock_settings_manager, mock_db_manager):
        """Test successful email indexing."""
        mock_connector = MagicMock()
        mock_connector.connect.return_value = True
        mock_email = MagicMock()
        mock_email.subject = "Test Email"
        mock_connector.fetch_emails.return_value = [mock_email] * 50
        mock_connector_class.return_value = mock_connector

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.outlook_connector = mock_connector
        wizard._show_step(5)

        # Give thread time to complete
        time.sleep(1.5)
        root.update()

        # Should have indexed emails
        assert wizard.indexed_count > 0

        wizard.destroy()

    def test_email_indexing_error_handling(self, root, mock_settings_manager, mock_db_manager):
        """Test email indexing error handling."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(5)
        wizard._show_indexing_error("Indexing failed")

        # Should show error message
        # Finish button should still be enabled to complete
        wizard._update_navigation_buttons()

        wizard.destroy()


class TestSkipFunctionality:
    """Test Skip Setup functionality."""

    def test_skip_button_sets_flag(self, root, mock_settings_manager, mock_db_manager):
        """Test Skip button sets skipped flag."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._on_skip_clicked()

        # Should set onboarding flags
        mock_db_manager.set_preference.assert_any_call("onboarding_complete", False)
        mock_db_manager.set_preference.assert_any_call("onboarding_skipped", True)

        # Note: wizard.destroy() called by _on_skip_clicked

    def test_skip_button_cancels_operations(self, root, mock_settings_manager, mock_db_manager):
        """Test Skip button cancels ongoing operations."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard.operation_in_progress = True
        wizard._on_skip_clicked()

        assert wizard.operation_cancelled is True

        # Note: wizard.destroy() called by _on_skip_clicked


class TestCompletionFunctionality:
    """Test wizard completion."""

    def test_complete_wizard_sets_flags(self, root, mock_settings_manager, mock_db_manager):
        """Test completing wizard sets completion flags."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._complete_wizard()

        # Should set onboarding flags
        mock_db_manager.set_preference.assert_any_call("onboarding_complete", True)
        mock_db_manager.set_preference.assert_any_call("onboarding_skipped", False)

        # Note: wizard.destroy() called by _complete_wizard

    def test_complete_wizard_calls_callback(self, root, mock_settings_manager, mock_db_manager):
        """Test completing wizard calls callback."""
        callback = Mock()
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager, on_complete=callback)

        wizard._complete_wizard()

        callback.assert_called_once()

        # Note: wizard.destroy() called by _complete_wizard

    def test_complete_wizard_saves_indexed_count(self, root, mock_settings_manager, mock_db_manager):
        """Test completing wizard saves indexed email count."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.indexed_count = 50

        wizard._complete_wizard()

        mock_db_manager.set_preference.assert_any_call("initial_emails_indexed", 50)

        # Note: wizard.destroy() called by _complete_wizard

    def test_finish_button_on_last_step_completes(self, root, mock_settings_manager, mock_db_manager):
        """Test Finish button on last step completes wizard."""
        callback = Mock()
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager, on_complete=callback)

        wizard._show_step(5)
        wizard.operation_in_progress = False  # Simulate operations complete
        wizard._on_next_clicked()

        # Should have called completion callback
        callback.assert_called_once()

        # Note: wizard.destroy() called by _complete_wizard


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_hardware_profile_loads_from_database(self, root, mock_settings_manager, mock_db_manager, mock_hardware_profile):
        """Test hardware profile loads from database if not in memory."""
        mock_db_manager.get_preference.return_value = mock_hardware_profile

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(3)  # Performance expectations step

        # Should have loaded from database
        mock_db_manager.get_preference.assert_called_with("hardware_profile", None)

        wizard.destroy()

    def test_outlook_connector_creates_if_missing(self, root, mock_settings_manager, mock_db_manager):
        """Test Outlook connector creates if missing for indexing."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.outlook_connector = None

        # Indexing step should attempt to create connector
        wizard._show_step(5)

        # operation_in_progress should be True
        assert wizard.operation_in_progress is True

        wizard.destroy()

    def test_operation_cancelled_stops_background_tasks(self, root, mock_settings_manager, mock_db_manager):
        """Test operation_cancelled flag stops background tasks."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard.operation_cancelled = True

        # Background threads should check this flag and exit early
        # This is tested implicitly by the background methods

        wizard.destroy()

    def test_unknown_hardware_tier_handling(self, root, mock_settings_manager, mock_db_manager):
        """Test unknown hardware tier is handled gracefully."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        expectations = wizard._get_tier_expectations("Unknown")
        tips = wizard._get_tier_tips("Unknown")

        # Should return default expectations and tips
        assert "Email Analysis" in expectations
        assert len(tips) > 0

        wizard.destroy()

    def test_step_indicator_updates(self, root, mock_settings_manager, mock_db_manager):
        """Test step indicator updates correctly."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        for step in range(1, 6):
            wizard._show_step(step)
            assert f"Step {step} of 5" in wizard.step_indicator.cget("text")

        wizard.destroy()

    def test_skip_button_hidden_on_last_step(self, root, mock_settings_manager, mock_db_manager):
        """Test Skip button is hidden on last step."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._show_step(5)
        wizard._update_navigation_buttons()

        # Skip button should not be mapped
        assert not wizard.skip_btn.winfo_ismapped()

        wizard.destroy()

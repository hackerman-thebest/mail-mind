"""
Integration tests for Onboarding Flow.

Tests Story 2.5: Complete onboarding flow including wizard, feature tour,
and integration with DatabaseManager and SettingsManager.
"""

import pytest
import customtkinter as ctk
from unittest.mock import Mock, patch, MagicMock
import time

from mailmind.ui.dialogs.onboarding_wizard import OnboardingWizard
from mailmind.ui.dialogs.feature_tour import FeatureTour
from mailmind.ui.dialogs.settings_dialog import SettingsDialog
from mailmind.database.database_manager import DatabaseManager
from mailmind.core.settings_manager import SettingsManager


@pytest.fixture
def root():
    """Create root window for tests."""
    root = ctk.CTk()
    yield root
    root.destroy()


@pytest.fixture
def mock_db_manager():
    """Create mock DatabaseManager."""
    mock = MagicMock(spec=DatabaseManager)
    mock.preferences = {}

    def get_pref(key, default=None):
        return mock.preferences.get(key, default)

    def set_pref(key, value):
        mock.preferences[key] = value
        return True

    mock.get_preference = Mock(side_effect=get_pref)
    mock.set_preference = Mock(side_effect=set_pref)

    return mock


@pytest.fixture
def mock_settings_manager():
    """Create mock SettingsManager."""
    mock = MagicMock(spec=SettingsManager)
    return mock


class TestOnboardingWizardToFeatureTour:
    """Test transition from OnboardingWizard to FeatureTour."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_complete_wizard_launches_feature_tour(
        self, mock_connector, mock_profiler, root, mock_settings_manager, mock_db_manager
    ):
        """Test completing wizard can launch feature tour."""
        # Mock hardware profile
        mock_profiler.detect_hardware.return_value = {
            "cpu_cores": 8,
            "ram_total_gb": 16.0,
            "hardware_tier": "Optimal"
        }

        # Mock Outlook connector
        mock_connector_instance = MagicMock()
        mock_connector_instance.connect.return_value = True
        mock_connector.return_value = mock_connector_instance

        tour_launched = Mock()

        def on_wizard_complete():
            """Simulate launching feature tour after wizard."""
            tour = FeatureTour(root, on_complete=Mock())
            tour_launched()
            tour.destroy()

        wizard = OnboardingWizard(
            root,
            mock_settings_manager,
            mock_db_manager,
            on_complete=on_wizard_complete
        )

        # Complete wizard
        wizard._complete_wizard()

        # Should have launched tour
        tour_launched.assert_called_once()

        # Database should have onboarding_complete flag
        assert mock_db_manager.preferences.get("onboarding_complete") is True


class TestOnboardingWithDatabase:
    """Test OnboardingWizard integration with DatabaseManager."""

    def test_wizard_saves_onboarding_complete_flag(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard saves onboarding_complete flag to database."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._complete_wizard()

        # Should have saved flags
        assert mock_db_manager.preferences.get("onboarding_complete") is True
        assert mock_db_manager.preferences.get("onboarding_skipped") is False

    def test_wizard_saves_hardware_profile(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard saves hardware profile to database."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        hardware_profile = {
            "cpu_cores": 8,
            "ram_total_gb": 16.0,
            "hardware_tier": "Optimal"
        }

        wizard.hardware_profile = hardware_profile
        wizard._show_step(2)
        wizard._show_hardware_results(1.5)

        # Should have saved profile
        assert "hardware_profile" in mock_db_manager.preferences

    def test_wizard_saves_indexed_count(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard saves indexed email count to database."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard.indexed_count = 50
        wizard._complete_wizard()

        # Should have saved count
        assert mock_db_manager.preferences.get("initial_emails_indexed") == 50

    def test_wizard_skip_saves_skip_flag(self, root, mock_settings_manager, mock_db_manager):
        """Test skipping wizard saves skip flag to database."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        wizard._on_skip_clicked()

        # Should have saved skip flags
        assert mock_db_manager.preferences.get("onboarding_complete") is False
        assert mock_db_manager.preferences.get("onboarding_skipped") is True

    def test_performance_step_loads_hardware_from_database(
        self, root, mock_settings_manager, mock_db_manager
    ):
        """Test performance expectations step loads hardware profile from database."""
        hardware_profile = {
            "cpu_cores": 8,
            "ram_total_gb": 16.0,
            "hardware_tier": "Optimal"
        }

        mock_db_manager.preferences["hardware_profile"] = hardware_profile

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(3)  # Performance expectations step

        # Should have loaded from database
        mock_db_manager.get_preference.assert_called_with("hardware_profile", None)


class TestSettingsDialogRerunWizard:
    """Test re-running wizard from Settings dialog."""

    def test_settings_dialog_has_rerun_wizard_option(self, root):
        """Test Settings dialog has re-run wizard option."""
        dialog = SettingsDialog(root)

        # Should have on_rerun_wizard_callback attribute
        assert hasattr(dialog, 'on_rerun_wizard_callback')

        dialog.destroy()

    def test_settings_dialog_rerun_wizard_callback(self, root, mock_settings_manager, mock_db_manager):
        """Test re-run wizard callback is called."""
        wizard_launched = Mock()

        def on_rerun_wizard():
            """Simulate launching wizard from settings."""
            wizard = OnboardingWizard(
                root,
                mock_settings_manager,
                mock_db_manager,
                on_complete=Mock()
            )
            wizard_launched()
            wizard.destroy()

        dialog = SettingsDialog(root, on_rerun_wizard=on_rerun_wizard)

        # Trigger re-run wizard
        dialog._on_rerun_wizard_clicked()

        # Should have launched wizard
        wizard_launched.assert_called_once()


class TestCompleteOnboardingFlow:
    """Test complete onboarding flow end-to-end."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    @patch('mailmind.ui.dialogs.onboarding_wizard.OutlookConnector')
    def test_full_onboarding_flow(
        self, mock_connector, mock_profiler, root, mock_settings_manager, mock_db_manager
    ):
        """Test complete flow: wizard -> feature tour -> complete."""
        # Mock hardware profile
        mock_profiler.detect_hardware.return_value = {
            "cpu_cores": 8,
            "ram_total_gb": 16.0,
            "ram_available_gb": 8.0,
            "gpu_detected": True,
            "gpu_vram_gb": 8.0,
            "hardware_tier": "Optimal",
            "expected_tokens_per_second": 150,
            "recommended_model": "llama3:8b"
        }

        # Mock Outlook connector
        mock_connector_instance = MagicMock()
        mock_connector_instance.connect.return_value = True
        mock_status = MagicMock()
        mock_status.status = "Connected"
        mock_status.email_address = "test@example.com"
        mock_connector_instance.get_connection_status.return_value = mock_status
        mock_connector.return_value = mock_connector_instance

        flow_complete = Mock()

        def on_wizard_complete():
            """Launch feature tour after wizard."""
            tour = FeatureTour(root, on_complete=on_tour_complete)
            tour.destroy()

        def on_tour_complete():
            """Mark flow as complete."""
            flow_complete()

        # Start wizard
        wizard = OnboardingWizard(
            root,
            mock_settings_manager,
            mock_db_manager,
            on_complete=on_wizard_complete
        )

        # Simulate completing wizard
        wizard.hardware_profile = mock_profiler.detect_hardware.return_value
        wizard.indexed_count = 50
        wizard._complete_wizard()

        # Flow should be complete
        assert mock_db_manager.preferences.get("onboarding_complete") is True
        assert mock_db_manager.preferences.get("initial_emails_indexed") == 50
        assert "hardware_profile" in mock_db_manager.preferences


class TestOnboardingStateManagement:
    """Test onboarding state management across components."""

    def test_first_run_detection(self, root, mock_settings_manager, mock_db_manager):
        """Test detecting first run (no onboarding_complete flag)."""
        # First run - no flag
        assert mock_db_manager.preferences.get("onboarding_complete") is None

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._complete_wizard()

        # After wizard - flag should be set
        assert mock_db_manager.preferences.get("onboarding_complete") is True

    def test_skip_vs_complete_state(self, root, mock_settings_manager, mock_db_manager):
        """Test different states for skip vs complete."""
        # Test skip
        wizard1 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard1._on_skip_clicked()

        assert mock_db_manager.preferences.get("onboarding_complete") is False
        assert mock_db_manager.preferences.get("onboarding_skipped") is True

        # Reset
        mock_db_manager.preferences.clear()

        # Test complete
        wizard2 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard2._complete_wizard()

        assert mock_db_manager.preferences.get("onboarding_complete") is True
        assert mock_db_manager.preferences.get("onboarding_skipped") is False

    def test_rerun_wizard_after_skip(self, root, mock_settings_manager, mock_db_manager):
        """Test re-running wizard after skipping."""
        # Skip wizard
        wizard1 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard1._on_skip_clicked()

        assert mock_db_manager.preferences.get("onboarding_skipped") is True

        # Re-run wizard
        wizard2 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard2._complete_wizard()

        # Should now be complete
        assert mock_db_manager.preferences.get("onboarding_complete") is True
        assert mock_db_manager.preferences.get("onboarding_skipped") is False


class TestFeatureTourIntegration:
    """Test FeatureTour integration with onboarding flow."""

    def test_feature_tour_after_wizard(self, root, mock_settings_manager, mock_db_manager):
        """Test launching feature tour after wizard completion."""
        wizard_complete = Mock()
        tour_complete = Mock()

        def on_wizard_complete():
            wizard_complete()
            tour = FeatureTour(root, on_complete=on_tour_complete)
            tour.destroy()

        def on_tour_complete():
            tour_complete()

        wizard = OnboardingWizard(
            root,
            mock_settings_manager,
            mock_db_manager,
            on_complete=on_wizard_complete
        )

        wizard._complete_wizard()

        # Both should have completed
        wizard_complete.assert_called_once()
        tour_complete.assert_called_once()

    def test_feature_tour_can_be_skipped(self, root):
        """Test feature tour can be skipped."""
        tour_complete = Mock()
        tour = FeatureTour(root, on_complete=tour_complete)

        tour._on_skip_clicked()

        # Should have called completion callback
        tour_complete.assert_called_once()

    def test_feature_tour_replay_from_help_menu(self, root):
        """Test feature tour can be replayed from Help menu."""
        # Simulate first tour
        tour1 = FeatureTour(root, on_complete=Mock())
        tour1._complete_tour()

        # Simulate replay from Help menu
        tour2 = FeatureTour(root, on_complete=Mock())

        # Should start from beginning
        assert tour2.current_slide == 0
        assert tour2.total_slides == 4

        tour2.destroy()


class TestHardwareProfilePersistence:
    """Test hardware profile persistence across components."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    def test_hardware_profile_saved_and_loaded(
        self, mock_profiler, root, mock_settings_manager, mock_db_manager
    ):
        """Test hardware profile is saved and can be loaded."""
        hardware_profile = {
            "cpu_cores": 8,
            "ram_total_gb": 16.0,
            "hardware_tier": "Optimal"
        }

        mock_profiler.detect_hardware.return_value = hardware_profile

        # Save during wizard
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard.hardware_profile = hardware_profile
        wizard._show_step(2)
        wizard._show_hardware_results(1.5)

        # Load in different wizard instance (e.g., re-run)
        wizard2 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard2._show_step(3)  # Performance expectations step should load profile

        # Should have loaded from database
        mock_db_manager.get_preference.assert_called_with("hardware_profile", None)

        wizard.destroy()
        wizard2.destroy()


class TestThreadSafety:
    """Test thread-safe operations in wizard."""

    @patch('mailmind.ui.dialogs.onboarding_wizard.HardwareProfiler')
    def test_hardware_detection_thread_safety(
        self, mock_profiler, root, mock_settings_manager, mock_db_manager
    ):
        """Test hardware detection uses thread-safe UI updates."""
        mock_profiler.detect_hardware.return_value = {
            "cpu_cores": 8,
            "hardware_tier": "Optimal"
        }

        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(2)

        # Should have started background operation
        assert wizard.operation_in_progress is True

        # Give thread time to complete
        time.sleep(1.0)
        root.update()

        # Operation should be complete
        assert wizard.operation_in_progress is False

        wizard.destroy()

    def test_operation_cancellation(self, root, mock_settings_manager, mock_db_manager):
        """Test background operations can be cancelled."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard._show_step(2)  # Start hardware detection

        wizard.operation_in_progress = True
        wizard._on_skip_clicked()

        # Should have set cancellation flag
        assert wizard.operation_cancelled is True


class TestEdgeCasesIntegration:
    """Test edge cases in integrated flow."""

    def test_wizard_without_hardware_detection(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard can complete even if hardware detection fails."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        # Skip hardware detection step
        wizard._show_step(3)  # Go to performance expectations
        wizard._show_step(5)  # Go to final step

        # Should still be able to complete
        wizard._complete_wizard()

        assert mock_db_manager.preferences.get("onboarding_complete") is True

    def test_wizard_without_outlook_connection(self, root, mock_settings_manager, mock_db_manager):
        """Test wizard can complete even if Outlook connection fails."""
        wizard = OnboardingWizard(root, mock_settings_manager, mock_db_manager)

        # Skip to final step
        wizard._show_step(5)

        # Should still be able to complete
        wizard._complete_wizard()

        assert mock_db_manager.preferences.get("onboarding_complete") is True

    def test_multiple_wizard_completions(self, root, mock_settings_manager, mock_db_manager):
        """Test multiple wizard completions (re-run from settings)."""
        # First completion
        wizard1 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard1.indexed_count = 50
        wizard1._complete_wizard()

        assert mock_db_manager.preferences.get("initial_emails_indexed") == 50

        # Second completion (re-run)
        wizard2 = OnboardingWizard(root, mock_settings_manager, mock_db_manager)
        wizard2.indexed_count = 75
        wizard2._complete_wizard()

        # Should update count
        assert mock_db_manager.preferences.get("initial_emails_indexed") == 75
